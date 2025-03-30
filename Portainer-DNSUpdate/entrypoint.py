#!/usr/bin/python3
import json
import os
from time import sleep

import requests
from deepdiff import DeepDiff

log_level = os.getenv("LOG_LEVEL", "INFO").upper()
dns_zone = os.getenv("DNS_ZONE")

portainer_api_endpoint = os.getenv("PORTAINER_API_ENDPOINT")
portainer_api_token = os.getenv("PORTAINER_API_TOKEN")

powerdns_api_endpoint = os.getenv("POWERDNS_API_ENDPOINT")
powerdns_api_token = os.getenv("POWERDNS_API_TOKEN")

if not (dns_zone and portainer_api_endpoint and portainer_api_token and powerdns_api_endpoint and powerdns_api_token):
    raise ValueError("Please set the required environment variables: DNS_ZONE, PORTAINER_API_ENDPOINT, "
                     "PORTAINER_API_TOKEN, POWERDNS_API_ENDPOINT, POWERDNS_API_TOKEN")

rrsets_cache = []

while True:
    sleep(5)
    try:
        response = requests.get(portainer_api_endpoint + "/endpoints", headers={"X-API-Key": portainer_api_token})

        if response.status_code != 200:
            err_msg = "Error: Unable to fetch endpoints\n"
            err_msg += f"Status Code: {response.status_code}\n"
            err_msg += f"Response: {response.text}\n"
            raise Exception(err_msg)

        endpoints = response.json()

        rrsets = []

        for endpoint in endpoints:
            domain_name = endpoint["Name"].replace(" ", "-").replace(".", "-") + "." + dns_zone
            for container in endpoint["Snapshots"][0]["DockerSnapshotRaw"]["Containers"]:
                fqdn = f"{container["Id"][:6]}.{domain_name}"
                for name in container["Names"]:
                    rrsets.append({
                        "name": f"{name.replace("/", "")}.{domain_name}",
                        "type": "CNAME",
                        "ttl": 60,
                        "changetype": "REPLACE",
                        "records": [
                            {
                                "content": fqdn,
                                "disabled": False
                            }
                        ]
                    })

                A_rrset = {
                    "name": fqdn,
                    "type": "A",
                    "ttl": 60,
                    "changetype": "REPLACE",
                    "records": []
                }

                AAAA_rrset = {
                    "name": fqdn,
                    "type": "AAAA",
                    "ttl": 60,
                    "changetype": "REPLACE",
                    "records": []
                }

                for network in container["NetworkSettings"]["Networks"]:
                    ip = container["NetworkSettings"]["Networks"][network]["IPAddress"]
                    if ip:
                        A_rrset["records"].append({
                            "content": ip,
                            "disabled": False
                        })

                    ipv6 = container["NetworkSettings"]["Networks"][network]["GlobalIPv6Address"]
                    if ipv6:
                        AAAA_rrset["records"].append({
                            "content": ipv6,
                            "disabled": False
                        })

                if A_rrset["records"]:
                    rrsets.append(A_rrset)
                if AAAA_rrset["records"]:
                    rrsets.append(AAAA_rrset)

        change = DeepDiff(rrsets_cache, rrsets, ignore_order=True)
        if not change:
            print("No change detected")
            continue

        print(change)

        response = requests.get(powerdns_api_endpoint, headers={"X-API-Key": powerdns_api_token})
        if response.status_code != 200:
            err_msg = "Error: Unable to fetch DNS zone details\n"
            err_msg += f"Status Code: {response.status_code}\n"
            err_msg += f"Response: {response.text}\n"
            raise Exception(err_msg)

        dns_zone_details = response.json()

        delta_rrsets = list(map(lambda r: {"name": r["name"], "type": r["type"], "changetype": "DELETE"},
                          filter(lambda r: r["type"] == "A" or r["type"] == "AAAA" or r["type"] == "CNAME",
                                 dns_zone_details["rrsets"]))).extend(rrsets)

        response = requests.patch(powerdns_api_endpoint, data=json.dumps({"rrsets": rrsets}),
                                  headers={"X-API-Key": powerdns_api_token, "Content-Type": "application/json"})
        if response.status_code != 204:
            err_msg = "Error: Unable to update records\n"
            err_msg += f"Status Code: {response.status_code}\n"
            err_msg += f"Response: {response.text}\n"
            raise Exception(err_msg)

        response = requests.put(powerdns_api_endpoint + "/rectify", headers={"X-API-Key": powerdns_api_token})
        if response.status_code != 200:
            err_msg = "Error: Unable to rectify records\n"
            err_msg += f"Status Code: {response.status_code}\n"
            err_msg += f"Response: {response.text}\n"
            raise Exception(err_msg)

        rrsets_cache = rrsets

    except Exception as err:
        print(err)
        continue

