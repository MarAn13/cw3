from pydub import AudioSegment
from argparse import ArgumentParser

params = {
    'INPUT_FORMAT': 'mp4',
    'MIN_SILENCE_LEN': 1000,
    'SILENCE_THRESHOLD': -16,
    'MIN_SPLIT_LEN': 6,
    'OUTPUT_FORMAT': 'mp4'
}


def split(filepath):
    audio = AudioSegment.from_file(filepath,
                                   params['INPUT_FORMAT'])
    duration = audio.duration_seconds
    if duration > params['MIN_SPLIT_LEN']:
        from pydub import silence, utils
        dBFS = audio.dBFS
        audio_chunks = silence.split_on_silence(audio,
                                                min_silence_len=params['MIN_SILENCE_LEN'],
                                                silence_thresh=dBFS + params['SILENCE_THRESHOLD'])
        print('silence_chunks: ', len(audio_chunks))
        processed_chunks = []
        for i in audio_chunks:
            if i.duration_seconds > params['MIN_SPLIT_LEN']:
                chunks = utils.make_chunks(i, params['MIN_SPLIT_LEN'])
                processed_chunks.extend(chunks)
            else:
                processed_chunks.append(i)
        print('processed_chunks: ', len(processed_chunks))
        for i, chunk in enumerate(processed_chunks):
            filename = f'{filepath.split(".")[-2]}_chunk_{i}.{params["OUTPUT_FORMAT"]}'
            chunk.export(filename, format=params['OUTPUT_FORMAT'])


def main():
    parser = ArgumentParser()
    parser.add_argument('path', type=str, help='file absolute path')
    args = parser.parse_args()
    split(args.path)
    print('done')


if __name__ == '__main__':
    main()
