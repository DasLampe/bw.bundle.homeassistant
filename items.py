import os
import pathlib

global node
import yaml

cfg = node.metadata.get('homeassistant')
user = cfg.get('user')
group = cfg.get('group')

svc_systemd = {
    f'homeassistant.service': {
        'enabled': True,
        'running': True,
        'needs': [
            f'file:/etc/systemd/system/homeassistant.service',
            'pkg_pip:',
            'tag:homeassistant_configs',
        ],
    }
}

files = {
    '/etc/systemd/system/homeassistant.service': {
        'source': 'etc/systemd/system/homeassistant.service.j2',
        'content_type': 'jinja2',
        'owner': 'root',
        'group': 'root',
    },
}

directories = {
    '/srv/homeassistant': {
        'owner': user,
        'group': group,
        'needs': [
            f'user:{user}',
        ],
    },
    f'/home/{user}/.homeassistant': {
        'owner': user,
        'group': group,
        'needs': [
            f'user:{user}',
        ]
    },
}

actions = {
    'create_venv': {
        'command': 'python3 -m venv /srv/homeassistant',
        'needs': [
            'directory:/srv/homeassistant',
            f'user:{user}',
            'pkg_apt:',
        ],
        'triggers': [
            'action:chown_venv',
        ],
        'unless': 'test -f /srv/homeassistant/bin/pip'
    },
    'chown_venv': {
        'command': f'chown -R {user}:{group} /srv/homeassistant',
        'triggered': True,
    },
    'install_venv_wheel': {
        'command': 'bash -c "source /srv/homeassistant/bin/activate && python3 -m pip install wheel"',
        'needs': [
            'action:create_venv',
            'action:chown_venv',
        ],
        'unless': 'test -f /srv/homeassistant/bin/wheel',
    },
    'cleanup_chown_venv': {
        'command': f'chown -R {user}:{group} /srv/homeassistant',
        'triggered': True,
    }
}

pkg_pip = {
    '/srv/homeassistant/homeassistant': {
        'version': cfg.get('version'),
        'needs': [
            'action:install_venv_wheel',
            'pkg_pip:/srv/homeassistant/urllib3', # Fix https://github.com/home-assistant/core/issues/95192
        ],
        'triggers': [
            f'svc_systemd:homeassistant.service:restart',
            'action:cleanup_chown_venv',
        ],
    },
    '/srv/homeassistant/urllib3': {
        'version': '1.26.16',
        'needs': [
            'action:install_venv_wheel',
        ]
    }
}

# Gather files from /data/homeassistant/files/{node.name}/ and copy them to /home/{user}/.homeassistant recursively
root_dir = os.path.join(node.repo.data_dir, 'homeassistant', 'files', node.name)
for current_dir, subdirs, subfiles in os.walk( root_dir ):
    relpath = os.path.relpath(current_dir, root_dir)

    # Directories
    for dirname in subdirs:
        dir_path = os.path.join(relpath, dirname)
        act_path = os.path.normpath(os.path.join('/home', user, '.homeassistant', dir_path))
        need_dir = os.path.normpath(os.path.join('/home', user, '.homeassistant', relpath))

        directories[act_path] = {
            'owner': user,
            'group': group,
            'tags': [
                'homeassistant_config_dirs',
            ],
            'needs': [
                f'directory:{need_dir}',
            ]
        }

    # Files
    for filename in subfiles:
        rel_filename = os.path.normpath(os.path.join(relpath, filename))
        act_filename = os.path.normpath(os.path.join('/home', user, '.homeassistant', rel_filename))
        need_dir = os.path.normpath(os.path.join('/home', user, '.homeassistant', relpath))

        files[act_filename] = {
            'source': os.path.normpath(os.path.join(node.name, rel_filename)),
            'owner': user,
            'group': group,
            'needs': [
                f'directory:{need_dir}',
            ],
            'triggers': [
                'svc_systemd:homeassistant.service:restart',
            ],
            'tags': [
                'homeassistant_configs'
            ]
        }
