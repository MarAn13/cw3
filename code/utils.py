import ffmpeg
from argparse import ArgumentParser
from pydub import AudioSegment
import torch.tensor
import os
import numpy as np
from other.deep_avsr.audio_only.util import predict as pred_audio_only
from other.deep_avsr.video_only.util import predict as pred_video_only
from other.deep_avsr.audio_visual.util import predict as pred_audio_video
from other.deep_avsr.audio_visual.config import args
from other.deep_avsr.audio_visual.utils.metrics import compute_wer as get_wer

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
        processed_time.append([temp_start, duration])
        processed_chunks = []
        temp = []
        chunk_duration = 0
        for start, stop in processed_time:
            temp_duration = stop - start
            if chunk_duration + temp_duration < params['MIN_SPLIT_LEN']:
                temp.append([start, stop])
                chunk_duration += temp_duration
            else:
                if len(temp) == 0:
                    temp = [[start, stop]]
                processed_chunks.append(temp)
                temp = []
                chunk_duration = 0
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


def split(filepath, overwrite=False):
    check_audio, check_video = check_streams(filepath)
    if not check_audio:
        processed_chunks = get_chunk_times_video(filepath)
    else:
        processed_chunks = get_chunk_times_audio(filepath)
    outputs = []
    for i, chunk in enumerate(processed_chunks):
        stream = None
        if np.sum([i[1] - i[0] for i in chunk]) < 1:
            continue
        for start, stop in chunk:
            temp_stream = ffmpeg.input(filepath, ss=start, to=stop)
            if stream is None:
                stream = temp_stream
            else:
                stream = ffmpeg.concat(temp_stream)
        output = f'temp/temp_chunk_{i}.mp4'
        stream = ffmpeg.output(stream, output)
        ffmpeg.run(stream, overwrite_output=True, quiet=True)
        outputs.append(output)
    if overwrite:
        os.remove(filepath)
    return outputs


def convert(filepath, mode, overwrite=False):
    check_audio, check_video = check_streams(filepath)
    output = filepath.split('.')
    output[-2] += '_output'
    output = '.'.join(output)
    stream = ffmpeg.input(filepath)
    if check_video and (mode == 'audio-video' or mode == 'video-only'):
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
        if check_audio and mode == 'audio-video':
            stream_audio = stream.audio
            stream = ffmpeg.concat(stream_video, stream_audio, v=1, a=1)
        else:
            stream = stream_video
    if check_video and check_audio and mode == 'audio-video':
        stream = ffmpeg.output(stream,
                               output,
                               f=params['OUTPUT_FORMAT'],
                               ac=params['AUDIO_CHANNELS'],
                               ar=params['AUDIO_SAMPLE_RATE'],
                               acodec=params['AUDIO_CODEC'],
                               crf=params['CRF'],
                               preset=params['PRESET']
                               )
    elif check_video and mode == 'video-only':
        stream = ffmpeg.output(stream,
                               output,
                               f=params['OUTPUT_FORMAT'],
                               crf=params['CRF'],
                               preset=params['PRESET']
                               )
    else:
        stream = ffmpeg.output(stream.audio,
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


def get_audio(filepath, output):
    stream_audio = ffmpeg.input(filepath).audio
    stream = ffmpeg.output(stream_audio,
                           output,
                           f=params['OUTPUT_FORMAT'])
    ffmpeg.run(stream, overwrite_output=True, quiet=True)


def predict(files, mode):
    if mode == 'audio-only':
        pred = pred_audio_only(files)
    elif mode == 'video-only':
        pred = pred_video_only(files)
    else:
        pred = pred_audio_video(files)
    return pred


def compute_wer(original, pred):
    original_batch = get_tensor_batch(original.upper())
    original_batch_len = torch.tensor(len(original_batch), dtype=torch.int32)
    pred_batch = get_tensor_batch(pred.upper())
    pred_batch_len = torch.tensor(len(pred_batch), dtype=torch.int32)
    wer = min(100,
              get_wer(pred_batch, original_batch, pred_batch_len, original_batch_len, args['CHAR_TO_INDEX'][' ']) * 100)
    return wer


def get_tensor_batch(data):
    batch = [args['CHAR_TO_INDEX'][i] for i in data]
    batch.append(args['CHAR_TO_INDEX']['<EOS>'])
    batch = torch.tensor(batch, dtype=torch.int32)
    return batch


def process_convert(files, mode):
    result = dict()
    for file in files:
        result[file] = []
        output = split(file)
        for i in output:
            result[file].append(convert(i, mode))
    return result


def main():
    parser = ArgumentParser()
    parser.add_argument('path', type=str, help='file absolute path')
    parser.add_argument('-o', action='store_true', help='overwrite current file')
    args = parser.parse_args()
    output = convert(args.path, args.o)
    split(output, args.o)
    print('done')


if __name__ == '__main__':
    # main()
    # print(compute_wer({'test': ['HELLO MY FRIEND NICE TO MEET YOU', 'HELLO MY FRIEND NICE TO MEET YOU'],
    #              'test1': ['HELLO MY FRIEND NICE TO MEET YOU', 'HELYU MY FRIND NCE TO MEIT U'],
    #              'test2': ['HELLO MY FRIEND NICE TO MEET YOU', 'HELLO FRIEND NECE TO MEET YOU']}))
    # print('audio_only',
    #       predict([r'C:\Users\marem\PycharmProjects\home\projects\cw3\app\code\other\demo\audio-only\test.mp4'],
    #               'audio-only'))
    # print('video_only',
    #       predict([r'C:\Users\marem\PycharmProjects\home\projects\cw3\app\code\other\demo\video-only\test5.mp4'],
    #               'video-only'))
    # print('audio_video',
    #       predict([r'C:\Users\marem\PycharmProjects\home\projects\cw3\app\code\other\demo\audio-video\test5.mp4'],
    #               'audio-video'))
    # print(
    #     process_convert([r'C:\Users\marem\PycharmProjects\home\projects\cw3\app\code\other\demo\audio-video\test5.mp4'],
    #                     'audio-video'))
    # print(process_convert([r'C:\Users\marem\PycharmProjects\home\projects\cw3\app\code\other\demo\audio-only\test2.mp4'], 'audio-only'))
    # print(process_convert([r'C:\Users\marem\PycharmProjects\home\projects\cw3\app\code\other\demo\video-only\test5.mp4']))
    # process_convert([r'C:\Users\marem\PycharmProjects\home\projects\cw3\app\code\temp\record.mp4'], 'audio-video')
    # print(process_convert([r'C:\Users\marem\Downloads\01-01-08-01-01-01-23_LU4qiu9L.mp4'], 'video-only', 0, 0.1))
    # preds = []
    # wers = []
    # temp = []
    # temp_means = []
    # temp_stds = []
    # for i in np.linspace(0, 1, 10):
    #     for j in np.linspace(0.1, 1, 10):
    #         temp.append([i, j])
    # pred_pred = 0
    # pred_count = 0
    # skip = False
    # last_mean = 0
    # np.random.shuffle(temp)
    # for temp_mean, temp_std in temp:
    #     if skip:
    #         if last_mean == temp_mean:
    #             continue
    #         else:
    #             skip = False
    #             pred_count = 0
    #     pred = predict({r'C:\Users\marem\Downloads\01-01-08-01-01-01-23_LU4qiu9L.mp4': [r'C:\Users\marem\Downloads\01-01-08-01-01-01-23_LU4qiu9L.mp4']},
    #                   'video-only', temp_mean, temp_std)[r'C:\Users\marem\Downloads\01-01-08-01-01-01-23_LU4qiu9L.mp4']
    #     wer = compute_wer('kids are talking by the door', pred)
    #     preds.append(pred)
    #     wers.append(wer)
    #     temp_means.append(temp_mean)
    #     temp_stds.append(temp_std)
    #     print(pred, wer, temp_mean, temp_std)
    #     if pred == pred_pred:
    #         pred_count += 1
    #     else:
    #         pred_count = 0
    #     if pred_count > 4:
    #         skip = True
    #         last_mean = temp_mean
    #     pred_pred = pred
    # test_wer = [wers[0], 0]
    # for i in range(len(wers)):
    #     if wers[i] < test_wer[0]:
    #         test_wer[0] = wers[i]
    #         test_wer[1] = i
    # print(preds[test_wer[1]], wers[test_wer[1]], temp_means[test_wer[1]], temp_stds[test_wer[1]])
    print('done')
