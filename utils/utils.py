import ffmpeg
from argparse import ArgumentParser
from pydub import AudioSegment
import os

params = {
    'INPUT_FORMAT': 'mp4',
    'MIN_SILENCE_LEN': 1000,
    'SILENCE_THRESHOLD': -30,
    'MIN_SPLIT_LEN': 6,
    'OUTPUT_FORMAT': 'mp4',
    'SILENCE_BUFFER': 250,
    'VIDEO_WIDTH': '160',
    'VIDEO_HEIGHT': '160',
    'VIDEO_FPS': 25,
    'CRF': 20,
    'PRESET': 'slower',
    'AUDIO_CHANNELS': 1,
    'AUDIO_SAMPLE_RATE': 16000,
    'AUDIO_CODEC': 'aac'
}


def check_streams(filepath):
    check_video = False
    check_audio = False
    try:
        check_stream = ffmpeg.probe(filepath)
        for i in check_stream['streams']:
            if i['codec_type'] == 'video':
                check_video = True
            if i['codec_type'] == 'audio':
                check_audio = True
    except ffmpeg.Error:
        pass
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
        processed_chunks = [[[0, duration]]]
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
    else:
        processed_chunks = [[[0, duration]]]
    return processed_chunks


def split(filepath, overwrite):
    check_audio, check_video = check_streams(filepath)
    if not check_audio:
        processed_chunks = get_chunk_times_video(filepath)
    else:
        processed_chunks = get_chunk_times_audio(filepath)
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
    if overwrite:
        os.remove(filepath)


def convert(filepath, overwrite):
    check_audio, check_video = check_streams(filepath)
    output = filepath.split('.')
    output[-2] += '_output'
    output = '.'.join(output)
    stream = ffmpeg.input(filepath)
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
    if overwrite:
        os.remove(filepath)
        os.rename(output, filepath)
        output = filepath
    return output


def merge(video, audio, output):
    stream_video = ffmpeg.input(video)
    stream_audio = ffmpeg.input(audio)
    stream = ffmpeg.concat(stream_video, stream_audio, v=1, a=1)
    stream = ffmpeg.output(stream,
                           output,
                           f=params['OUTPUT_FORMAT'])
    ffmpeg.run(stream, overwrite_output=True, quiet=True)


def main():
    parser = ArgumentParser()
    parser.add_argument('path', type=str, help='file absolute path')
    parser.add_argument('-o', action='store_true', help='overwrite current file')
    args = parser.parse_args()
    output = convert(args.path, args.o)
    split(output, args.o)
    print('done')


if __name__ == '__main__':
    main()
