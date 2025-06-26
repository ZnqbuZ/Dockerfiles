import yaml
import copy
import os

runners_dir = f"/var/lib/runners"

runner_group = "ec2"
scale = 4

docker_gid = 0
runner_url = ""
runner_token = ""

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
        'RUNNER_UID': 42000,
    }
}

for i in range(scale):
    runner_home = os.path.join(runners_dir, f'{runner_group}-{i}')

    current_runner = copy.deepcopy(runner)
    current_runner['volumes'].append(f"{runner_home}:{runner_home}")
    current_runner['environment']['RUNNER_NAME'] = f"{runner_group}-{i}"
    current_runner['environment']['RUNNER_HOME'] = runner_home

    compose['services'][f'{runner_group}-{i}'] = current_runner

with open('docker-compose.yml', 'w') as f:
    yaml.dump(compose, f, default_flow_style=False)