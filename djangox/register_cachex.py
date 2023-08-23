import os
import json
from pathlib import Path
from tools.base import get_project_name


def register(caches_config):
    config = {}
    for key, conf in caches_config.items():
        location = conf['LOCATION']
        location, db = location.rsplit('/', 1)
        location, port = location.rsplit(':', 1)
        location, host = location.rsplit('@', 1)
        _, password = location.rsplit(':', 1)
        config[key] = {
            'db': int(db), 'port': int(port),
            'host': str(host), 'password': str(password)
        }

    config_filepath = os.path.join(
        Path(__file__).resolve(strict=True).parent.parent,
        f'{get_project_name()}-config.json'
    )
    with open(config_filepath, 'w+') as fp:
        fp.write(json.dumps(config))
