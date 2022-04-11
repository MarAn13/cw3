from pathlib import Path

params = {
    'NETWORK_DIR': '../deep_avsr/',
    'AUDIO_ONLY_CONFIG': '../deep_avsr/audio_only/config.py',
    'VIDEO_ONLY_CONFIG': '../deep_avsr/video_only/config.py',
    'AUDIO_VIDEO_CONFIG': '../deep_avsr/audio_visual/config.py'
}


def check_files():
    return Path(params['NETWORK_DIR']).exists()


def setup():
    try:
        if not check_files():
            raise Exception('network directory was not found')

    except Exception as err:
        print(err)
setup()