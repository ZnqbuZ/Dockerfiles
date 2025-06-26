import yaml
import copy
import os
import argparse

parser = argparse.ArgumentParser(description="Generate a Docker Compose file for GitHub Actions runners.")

parser.add_argument("--dir", type=str, default="/var/lib/runners", help="Directory for runners")
parser.add_argument("--prefix", type=str, help="Prefix for runner names")
parser.add_argument("--scale", type=int, default=4, help="Number of runners to create")
parser.add_argument("--uid", type=int, help="UID for the runner user")
parser.add_argument("--docker-gid", type=int, help="GID for the Docker group on the host")
parser.add_argument("--url", type=str, help="URL of the GitHub Actions runner")
parser.add_argument("--token", type=str, help="Token for the GitHub Actions runner")

args = parser.parse_args()
runners_dir = args.dir
runner_group = args.prefix
scale = args.scale

runner_uid = args.uid
docker_gid = args.docker_gid
runner_url = args.url
runner_token = args.token

compose = {
    'services': {}
}

runner = {
    'image': 'znqbuz/actions-runner',
    'volumes': [
        '/var/run/docker.sock:/var/run/docker.sock',
    ],
    'environment': {
        'DOCKER_GID': docker_gid,
        'RUNNER_URL': runner_url,
        'RUNNER_TOKEN': runner_token,
    }
}

if runner_uid is not None:
    runner['environment']['RUNNER_UID'] = runner_uid

for i in range(scale):
    runner_home = os.path.join(runners_dir, f'{runner_group}-{i}')

    current_runner = copy.deepcopy(runner)
    current_runner['volumes'].append(f"{runner_home}:{runner_home}")
    current_runner['environment']['RUNNER_NAME'] = f"{runner_group}-{i}"
    current_runner['environment']['RUNNER_HOME'] = runner_home

    compose['services'][f'{runner_group}-{i}'] = current_runner

with open('docker-compose.yml', 'w') as f:
    yaml.dump(compose, f, default_flow_style=False)