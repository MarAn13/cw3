import ffmpeg
from argparse import ArgumentParser

params = {
    'VIDEO_WIDTH': '160',
    'VIDEO_HEIGHT': '160',
    'VIDEO_FPS': 25,
    'OUTPUT_FORMAT': 'mp4',
    'CRF': 20,
    'PRESET': 'slower',
    'AUDIO_CHANNELS': 1,
    'AUDIO_SAMPLE_RATE': 16000,
    'AUDIO_CODEC': 'aac'
}


def convert(filename):
    check_video = False
    check_audio = False
    check_stream = ffmpeg.probe(filename)
    for i in check_stream['streams']:
        if i['codec_type'] == 'video':
            check_video = True
        if i['codec_type'] == 'audio':
            check_audio = True
    output = filename.split('.')
    output[-2] += '_output'
    output = '.'.join(output)
    stream = ffmpeg.input(filename)
    if check_video:
        stream_video = stream.video
        stream_video = ffmpeg.filter(stream_video,
                                     'scale',
                                     width=params['VIDEO_WIDTH'],
                                     height=params['VIDEO_HEIGHT']
                                     )
        stream_video = ffmpeg.filter(stream_video,
                                     'fps',
                                     fps=params['VIDEO_FPS'],
                                     round='up'
                                     )
        if check_audio:
            stream_audio = stream.audio
            stream = ffmpeg.concat(stream_video, stream_audio, v=1, a=1)
        else:
            stream = stream_video
    if check_video and check_audio:
        stream = ffmpeg.output(stream,
                               output,
                               f=params['OUTPUT_FORMAT'],
                               ac=params['AUDIO_CHANNELS'],
                               ar=params['AUDIO_SAMPLE_RATE'],
                               acodec=params['AUDIO_CODEC'],
                               crf=params['CRF'],
                               preset=params['PRESET']
                               )
    elif check_video:
        stream = ffmpeg.output(stream,
                               output,
                               f=params['OUTPUT_FORMAT'],
                               crf=params['CRF'],
                               preset=params['PRESET']
                               )
    else:
        stream = ffmpeg.output(stream,
                               output,
                               f=params['OUTPUT_FORMAT'],
                               ac=params['AUDIO_CHANNELS'],
                               ar=params['AUDIO_SAMPLE_RATE'],
                               acodec=params['AUDIO_CODEC']
                               )
    ffmpeg.run(stream, overwrite_output=True, quiet=True)


def main():
    parser = ArgumentParser()
    parser.add_argument('path', type=str, help='file absolute path')
    args = parser.parse_args()
    convert(args.path)
    print('done')


if __name__ == '__main__':
    main()
