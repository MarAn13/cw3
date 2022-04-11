import ffmpeg
from pydub import AudioSegment
from argparse import ArgumentParser

params = {
    'INPUT_FORMAT': 'mp4',
    'MIN_SILENCE_LEN': 1000,
    'SILENCE_THRESHOLD': -30,
    'MIN_SPLIT_LEN': 6,
    'OUTPUT_FORMAT': 'mp4',
    'SILENCE_BUFFER': 250
}


def check_streams(filepath):
    check_video = False
    check_audio = False
    check_stream = ffmpeg.probe(filepath)
    for i in check_stream['streams']:
        if i['codec_type'] == 'video':
            check_video = True
        if i['codec_type'] == 'audio':
            check_audio = True
    return check_audio, check_video


def get_chunk_times_audio(filepath):
    audio = AudioSegment.from_file(filepath,
                                   params['INPUT_FORMAT'])
    duration = audio.duration_seconds
    if duration > params['MIN_SPLIT_LEN']:
        from pydub import silence
        dBFS = audio.dBFS
        silence_time = silence.detect_silence(audio,
                                              min_silence_len=params['MIN_SILENCE_LEN'],
                                              silence_thresh=dBFS + params['SILENCE_THRESHOLD'])
        silence_time = [[(start / 1000), (stop / 1000)] for start, stop in silence_time]  # ms to seconds
        temp = []
        for start, stop in silence_time:
            start_with_silence = start + params['SILENCE_BUFFER']
            stop_with_silence = stop - params['SILENCE_BUFFER']
            if start_with_silence < stop_with_silence:
                start = start_with_silence
                stop = stop_with_silence
            temp.append([start, stop])
        processed_time = []
        current_time = 0
        for start, stop in temp:
            temp_start = current_time
            while start - temp_start > params['MIN_SPLIT_LEN']:
                temp_stop = temp_start + params['MIN_SPLIT_LEN']
                processed_time.append([temp_start, temp_stop])
                temp_start = temp_stop
            processed_time.append([current_time, start])
            current_time = stop
        temp_start = current_time
        while duration - temp_start > params['MIN_SPLIT_LEN']:
            temp_stop = temp_start + params['MIN_SPLIT_LEN']
            processed_time.append([temp_start, temp_stop])
            temp_start = temp_stop
        processed_time.append([current_time, duration])
        print(processed_time)
        processed_chunks = []
        temp = []
        chunk_duration = 0
        for start, stop in processed_time:
            temp_duration = stop - start
            if chunk_duration + temp_duration < params['MIN_SPLIT_LEN']:
                temp.append([start, stop])
            else:
                processed_chunks.append(temp)
                temp = [[start, stop]]
                chunk_duration = 0
            chunk_duration += temp_duration
        processed_chunks.append(temp)
    else:
        processed_chunks = False
    print(processed_chunks)
    return processed_chunks


def get_chunk_times_video(filepath):
    duration = float((ffmpeg.probe(filepath)['streams'][0]['duration']))
    if duration > params['MIN_SPLIT_LEN']:
        processed_chunks = []
        current_time = 0
        while current_time < duration:
            end_time = current_time + params['MIN_SPLIT_LEN']
            if end_time > duration:
                end_time = duration
            processed_chunks.append([[current_time, end_time]])
        return processed_chunks


def split(filepath):
    check_audio, check_video = check_streams(filepath)
    if not check_audio:
        processed_chunks = get_chunk_times_video(filepath)
    else:
        processed_chunks = get_chunk_times_audio(filepath)
    if processed_chunks:
        for i, chunk in enumerate(processed_chunks):
            stream = None
            stream_audio = None
            stream_video = None
            for start, stop in chunk:
                temp_stream = ffmpeg.input(filepath, ss=start, to=stop)
                if stream is None:
                    stream = True
                    stream_video = temp_stream.video
                    stream_audio = temp_stream.audio
                else:
                    stream_video = ffmpeg.concat(stream_video, temp_stream.video, v=1, a=0)
                    stream_audio = ffmpeg.concat(stream_audio, temp_stream.audio, v=0, a=1)
            stream = ffmpeg.concat(stream_video, stream_audio, v=1, a=1)
            stream = ffmpeg.output(stream, f'{filepath.split(".")[-2]}_chunk_{i}.mp4')
            ffmpeg.run(stream, overwrite_output=True, quiet=True)


def main():
    parser = ArgumentParser()
    parser.add_argument('path', type=str, help='file absolute path')
    args = parser.parse_args()
    split(args.path)
    print('done')


if __name__ == '__main__':
    main()
