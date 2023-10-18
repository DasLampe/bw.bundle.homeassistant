global node

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
            f'directory:/home/{user}/.homeassistant',
        ],
    }
}

files = {
    '/etc/systemd/system/homeassistant.service': {
        'source': 'etc/systemd/system/homeassistant.service.j2',
        'content_type': 'jinja2',
        'owner': 'root',
        'group': 'root',
    }
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
    }
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
    # '/srv/homeassistant/pyqrcode': {
    #     'needs': [
    #         'action:install_venv_wheel',
    #     ],
    # },
    # '/srv/homeassistant/pyotp': {
    #     'needs': [
    #         'action:install_venv_wheel',
    #     ],
    # }
}
