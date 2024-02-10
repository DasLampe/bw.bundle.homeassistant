defaults = {
    'homeassistant': {
        'user': 'homeassistant',
        'group': 'homeassistant',
        'version': '2024.02.1',
    },
    'apt': {
        'packages': {
            'python3': {},
            'python3-dev': {},
            'python3-venv': {},
            'python3-pip': {},
            'bluez': {},
            'libffi-dev': {},
            'libssl-dev': {},
            'libjpeg-dev': {},
            'zlib1g-dev': {},
            'autoconf': {},
            'build-essential': {},
            'libopenjp2-7': {},
            'libtiff6': {},
            'libturbojpeg0-dev': {},
            'tzdata': {},
            'ffmpeg': {},
            'liblapack3': {},
            'liblapack-dev': {},
            'libatlas-base-dev': {},
        },
    },
}

@metadata_reactor
def add_homeassitant_user(metadata):
    if not node.has_bundle('users'):
        raise DoNotRunAgain

    return {
        'users': {
            metadata.get('homeassistant/user'): {
                'add_groups': [
                    'gpio',
                    'i2c',
                    'bluetooth'
                ],
                'shell': '/bin/nologin',
            },
        },
    }
