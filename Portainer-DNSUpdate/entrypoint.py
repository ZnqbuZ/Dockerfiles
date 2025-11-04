#!/usr/local/bin/python3
import json
import logging
import os
import signal
from time import sleep

import requests


def handle_sigterm(signum, frame):
    print("Received SIGTERM. Exiting...")
    exit(0)


signal.signal(signal.SIGTERM, handle_sigterm)

log_level = getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO)

check_interval = int(os.getenv("CHECK_INTERVAL", 15))

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
rrsets_cache_set = set()

while True:
    try:
        logger.debug("====================")
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

            logger.debug(f"CNAME for endpoint: {domain_name} -> {endpoint_fqdn}")
            rrsets.append(
                {
                    "name": domain_name,
                    "type": "CNAME",
                    "ttl": 60,
                    "changetype": "REPLACE",
                    "records": [{"content": endpoint_fqdn, "disabled": False}],
                }
            )

            for container in endpoint["Snapshots"][0]["DockerSnapshotRaw"].get("Containers", []):
                logger.debug(
                    f"\tContainer: {container["Names"]} @ {endpoint["Name"]} {container["Id"]}"
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
                        f"\t\tHost network found. Use CNAME record: {fqdn} -> {domain_name}"
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
                        logger.debug(f"\t\tIPv4 Address: {ip}")
                        A_rrset["records"].append({"content": ip, "disabled": False})

                    ipv6 = container["NetworkSettings"]["Networks"][network][
                        "GlobalIPv6Address"
                    ]
                    if ipv6:
                        logger.debug(f"\t\tIPv6 Address: {ipv6}")
                        AAAA_rrset["records"].append(
                            {"content": ipv6, "disabled": False}
                        )

                if A_rrset["records"]:
                    rrsets.append(A_rrset)
                if AAAA_rrset["records"]:
                    rrsets.append(AAAA_rrset)

        logger.debug("Detecting change...")

        rrsets_set = set(json.dumps(r, sort_keys=True) for r in rrsets)

        rrsets_added = rrsets_set - rrsets_cache_set
        rrsets_removed = rrsets_cache_set - rrsets_set

        if not (rrsets_added or rrsets_removed):
            logger.debug("No change detected.")
            continue

        logger.info("====================")
        logger.info("Change detected.")
        logger.info("--------------------")
        logger.info("Added")
        logger.info("--------------------")
        for r_str in rrsets_added:
            r = json.loads(r_str)
            logger.info(f"\t{r['name']} -> {[record['content'] for record in r['records']]}")
        logger.info("--------------------")
        logger.info("Removed")
        logger.info("--------------------")
        for r_str in rrsets_removed:
            r = json.loads(r_str)
            logger.info(f"\t{r['name']} -> {[record['content'] for record in r['records']]}")
        logger.info("--------------------")

        logger.debug("Retrieving zone info...")
        response = requests.get(
            powerdns_api_endpoint, headers={"X-API-Key": powerdns_api_token}
        )
        if response.status_code != 200:
            err_msg = "Error: Unable to fetch DNS zone details.\n"
            err_msg += f"Status Code: {response.status_code}\n"
            err_msg += f"Response: {response.text}\n"
            raise Exception(err_msg)

        dns_zone_details = response.json()

        delta_rrsets = [
            {
                "name": r["name"],
                "type": r["type"],
                "changetype": "DELETE",
            }
            for r in dns_zone_details["rrsets"]
            if r["type"] in ["A", "AAAA", "CNAME"]
        ]
        delta_rrsets.extend(rrsets)

        logger.debug("Updating records...")
        response = requests.patch(
            powerdns_api_endpoint,
            data=json.dumps({"rrsets": delta_rrsets}),
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

        logger.debug("Rectifying zone...")
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
        rrsets_cache_set = rrsets_set

    except Exception as err:
        logger.error(err, exc_info=logger.getEffectiveLevel() <= logging.INFO)
        continue

    finally:
        sleep(check_interval)
