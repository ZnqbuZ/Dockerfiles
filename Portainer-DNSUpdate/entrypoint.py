#!/usr/local/bin/python3
import json
import os
from time import sleep
import logging
import signal

import requests
from deepdiff import DeepDiff


def handle_sigterm(signum, frame):
    print("Received SIGTERM. Exiting...")
    exit(0)


signal.signal(signal.SIGTERM, handle_sigterm)

log_level = getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO)
dns_zone = os.getenv("DNS_ZONE")
base_zone = os.getenv("BASE_ZONE", dns_zone)

portainer_api_endpoint = os.getenv("PORTAINER_API_ENDPOINT")
portainer_api_token = os.getenv("PORTAINER_API_TOKEN")

powerdns_api_endpoint = os.getenv("POWERDNS_API_ENDPOINT")
powerdns_api_token = os.getenv("POWERDNS_API_TOKEN")

if not (
    dns_zone
    and portainer_api_endpoint
    and portainer_api_token
    and powerdns_api_endpoint
    and powerdns_api_token
):
    raise ValueError(
        "Please set the required environment variables: DNS_ZONE, PORTAINER_API_ENDPOINT, "
        "PORTAINER_API_TOKEN, POWERDNS_API_ENDPOINT, POWERDNS_API_TOKEN"
    )

logging.basicConfig(
    level=log_level,
    format="%(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

powerdns_api_endpoint += f"/servers/localhost/zones/{dns_zone}"

logger.info("Started.")

rrsets_cache = []

while True:
    sleep(5)
    try:
        logger.debug("Retrieving endpoints...")
        response = requests.get(
            portainer_api_endpoint + "/endpoints",
            headers={"X-API-Key": portainer_api_token},
        )

        if response.status_code != 200:
            err_msg = "Error: Unable to fetch endpoints.\n"
            err_msg += f"Status Code: {response.status_code}\n"
            err_msg += f"Response: {response.text}\n"
            raise Exception(err_msg)

        endpoints = response.json()

        logger.debug(f"Found: {[endpoint["Name"] for endpoint in endpoints]}")

        rrsets = []

        for endpoint in endpoints:
            domain_name = endpoint["Name"].replace(" ", "-") + "." + dns_zone
            endpoint_fqdn = endpoint["Name"].replace(" ", "-") + "." + base_zone

            logger.debug(f"CNAME for endpoint: {domain_name} ->")
            rrsets.append(
                {
                    "name": domain_name,
                    "type": "CNAME",
                    "ttl": 60,
                    "changetype": "REPLACE",
                    "records": [{"content": endpoint_fqdn, "disabled": False}],
                }
            )
            
            for container in endpoint["Snapshots"][0]["DockerSnapshotRaw"][
                "Containers"
            ]:
                logger.debug(
                    f"Container: {container["Names"]} @ {endpoint["Name"]} {container["Id"]}"
                )
                fqdn = f"{container["Id"][:6]}.{domain_name}"
                for name in container["Names"]:
                    rrsets.append(
                        {
                            "name": f"{name.replace("/", "")}.{domain_name}",
                            "type": "CNAME",
                            "ttl": 60,
                            "changetype": "REPLACE",
                            "records": [{"content": fqdn, "disabled": False}],
                        }
                    )

                if "host" in container["NetworkSettings"]["Networks"]:
                    logger.debug(
                        f"Host network found. Use CNAME record: {fqdn} -> {domain_name}"
                    )
                    rrsets.append(
                        {
                            "name": fqdn,
                            "type": "CNAME",
                            "ttl": 60,
                            "changetype": "REPLACE",
                            "records": [{"content": domain_name, "disabled": False}],
                        }
                    )
                    continue

                A_rrset = {
                    "name": fqdn,
                    "type": "A",
                    "ttl": 60,
                    "changetype": "REPLACE",
                    "records": [],
                }

                AAAA_rrset = {
                    "name": fqdn,
                    "type": "AAAA",
                    "ttl": 60,
                    "changetype": "REPLACE",
                    "records": [],
                }

                for network in container["NetworkSettings"]["Networks"]:
                    ip = container["NetworkSettings"]["Networks"][network]["IPAddress"]
                    if ip:
                        logger.debug(f"IPv4 Address: {ip}")
                        A_rrset["records"].append({"content": ip, "disabled": False})

                    ipv6 = container["NetworkSettings"]["Networks"][network][
                        "GlobalIPv6Address"
                    ]
                    if ipv6:
                        logger.debug(f"IPv6 Address: {ipv6}")
                        AAAA_rrset["records"].append(
                            {"content": ipv6, "disabled": False}
                        )

                if A_rrset["records"]:
                    rrsets.append(A_rrset)
                if AAAA_rrset["records"]:
                    rrsets.append(AAAA_rrset)

        logger.debug("Detecting change...")

        change = DeepDiff(rrsets_cache, rrsets, ignore_order=True)
        if not change:
            logger.debug("No change detected.")
            continue

        logger.info(change)

        logger.debug("Retriving zone info...")
        response = requests.get(
            powerdns_api_endpoint, headers={"X-API-Key": powerdns_api_token}
        )
        if response.status_code != 200:
            err_msg = "Error: Unable to fetch DNS zone details.\n"
            err_msg += f"Status Code: {response.status_code}\n"
            err_msg += f"Response: {response.text}\n"
            raise Exception(err_msg)

        dns_zone_details = response.json()

        delta_rrsets = list(
            map(
                lambda r: {
                    "name": r["name"],
                    "type": r["type"],
                    "changetype": "DELETE",
                },
                filter(
                    lambda r: r["type"] == "A"
                    or r["type"] == "AAAA"
                    or r["type"] == "CNAME",
                    dns_zone_details["rrsets"],
                ),
            )
        ).extend(rrsets)

        logger.info("Updating records...")
        response = requests.patch(
            powerdns_api_endpoint,
            data=json.dumps({"rrsets": rrsets}),
            headers={
                "X-API-Key": powerdns_api_token,
                "Content-Type": "application/json",
            },
        )
        if response.status_code != 204:
            err_msg = "Error: Unable to update records\n"
            err_msg += f"Status Code: {response.status_code}\n"
            err_msg += f"Response: {response.text}\n"
            raise Exception(err_msg)

        logger.info("Rectifying zone...")
        response = requests.put(
            powerdns_api_endpoint + "/rectify",
            headers={"X-API-Key": powerdns_api_token},
        )
        if response.status_code != 200:
            err_msg = "Error: Unable to rectify records.\n"
            err_msg += f"Status Code: {response.status_code}\n"
            err_msg += f"Response: {response.text}\n"
            raise Exception(err_msg)

        logger.info("Updated.")

        rrsets_cache = rrsets

    except Exception as err:
        logger.error(err, exc_info=logger.getEffectiveLevel() <= logging.INFO)
        continue
