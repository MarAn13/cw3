import ffmpeg
from argparse import ArgumentParser
from pydub import AudioSegment
import torch.tensor
import os
import numpy as np
import cv2 as cv
import shutil
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
    'SILENCE_BUFFER': 0.250,
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
    """
    checks for the presence of an audio and video channel
    :param filepath (str): filepath
    :return (bool): audio and video channel status
    """
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
    """
    splits an audio file into chunks
    :param filepath (str): filepath
    :return list(list(list(float, float))): chunks
    """
    audio = AudioSegment.from_file(filepath,
                                   params['INPUT_FORMAT'])
    duration = audio.duration_seconds
    if duration > params['MIN_SPLIT_LEN']:
        from pydub import silence
        dBFS = audio.dBFS
        silence_time = silence.detect_silence(audio, min_silence_len=params['MIN_SILENCE_LEN'],
                                              silence_thresh=dBFS + params['SILENCE_THRESHOLD'])
        silence_chunks = [[(start / 1000), (stop / 1000)] for start, stop in silence_time]  # ms to seconds
        chunks_without_silence = []
        current_time = 0
        for start, stop in silence_chunks:
            if start - current_time >= 1:
                chunks_without_silence.append([current_time, start + params['SILENCE_BUFFER']])
            current_time = stop - params['SILENCE_BUFFER']
        if duration - current_time >= 1:
            chunks_without_silence.append([current_time, duration])
        processed_chunks = []
        current_chunk = 0
        chunk_start = None
        chunk = []
        for start, stop in chunks_without_silence:
            while stop - start != 0:
                if chunk_start is None:
                    chunk_start = start
                if current_chunk + (stop - start) > params['MIN_SPLIT_LEN']:
                    if len(chunk) == 0:
                        processed_chunks.append(
                            [[chunk_start, chunk_start + current_chunk + (params['MIN_SPLIT_LEN'] - current_chunk)]])
                    else:
                        chunk.append([chunk_start, chunk_start + (params['MIN_SPLIT_LEN'] - current_chunk)])
                        processed_chunks.append(chunk)
                        chunk = []
                    start += (params['MIN_SPLIT_LEN'] - current_chunk)
                    chunk_start = None
                    current_chunk = 0
                else:
                    current_chunk += (stop - start)
                    start = stop
            if current_chunk != 0:
                chunk.append([chunk_start, chunk_start + current_chunk])
            chunk_start = None
        if len(chunk) != 0:
            processed_chunks.append(chunk)
    else:
        processed_chunks = [[[0, duration]]]
    return processed_chunks


def get_chunk_times_video(filepath):
    """
    splits a video file into chunks
    :param filepath (str): filepath
    :return list(list(list(float, float))): chunks
    """
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
    """
    split file driver
    :param filepath (str): filepath
    :param overwrite (bool): whether to delete original file
    :return list(str): output filepaths
    """
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
                stream = ffmpeg.concat(stream, temp_stream, a=1, v=1)
        output = filepath.split('\\')[-1].split('.')[-2]
        output = f'temp/{output}_chunk_{i}.mp4'
        stream = ffmpeg.output(stream, output)
        try:
            ffmpeg.run(stream, overwrite_output=True, quiet=True, capture_stdout=True, capture_stderr=True)
        except ffmpeg.Error as e:
            print('stdout:', e.stdout.decode('utf8'))
            print('stderr:', e.stderr.decode('utf8'))
        outputs.append(output)
    if overwrite:
        os.remove(filepath)
    return outputs


def convert(filepath, mode, overwrite=False):
    """
    converting the file to the appropriate format
    :param filepath (str): filepath
    :param mode (str): conversion type
    :param overwrite (bool): whether to delete original file
    :return (str): output filepath
    """
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
    """
    merges audio and video channels
    :param video (str): video filepath
    :param audio (str): audio filepath
    :param output (str): output filepath
    :return (str): output filepath
    """
    stream_video = ffmpeg.input(video)
    stream_audio = ffmpeg.input(audio)
    stream = ffmpeg.concat(stream_video, stream_audio, v=1, a=1)
    stream = ffmpeg.output(stream,
                           output,
                           f=params['OUTPUT_FORMAT'])
    ffmpeg.run(stream, overwrite_output=True, quiet=True)


def get_audio(filepath, output):
    """
    gets audio channel from file
    :param filepath (str): filepath
    :param output (str): output filepath
    :return (void):
    """
    stream_audio = ffmpeg.input(filepath).audio
    stream = ffmpeg.output(stream_audio,
                           output,
                           f=params['OUTPUT_FORMAT'])
    ffmpeg.run(stream, overwrite_output=True, quiet=True)


def predict(files, mode):
    """
    driver function for model prediction
    :param files (list(str)): filepaths
    :param mode (str): prediction mode
    :return (dict(str:str)): prediction result
    """
    if mode == 'audio-only':
        pred = pred_audio_only(files)
    elif mode == 'video-only':
        pred = pred_video_only(files)
    else:
        pred = pred_audio_video(files)
    return pred


def compute_wer(original, pred):
    """
    driver function for WER computing
    :param original (str): original text
    :param pred (str): prediction
    :return (float): WER result
    """
    original_batch = get_tensor_batch(original.upper())
    original_batch_len = torch.tensor(len(original_batch), dtype=torch.int32)
    pred_batch = get_tensor_batch(pred.upper())
    pred_batch_len = torch.tensor(len(pred_batch), dtype=torch.int32)
    wer = min(100,
              get_wer(pred_batch, original_batch, pred_batch_len, original_batch_len, args['CHAR_TO_INDEX'][' ']) * 100)
    return wer


def get_tensor_batch(data):
    """
    converts data to tensor
    :param data (str): data
    :return (tensor): data tensor
    """
    batch = [args['CHAR_TO_INDEX'][i] for i in data]
    batch.append(args['CHAR_TO_INDEX']['<EOS>'])
    batch = torch.tensor(batch, dtype=torch.int32)
    return batch


def process_convert(files, mode, SNR=100):
    """
    driver for processing and converting of files
    :param files (list(str)): filepaths
    :param mode (str): convertion mode
    :param SNR (float): SNR in dB
    :return (dict(str:list(str)): convertion result
    """
    result = dict()
    for file in files:
        result[file] = []
        temp = file
        if mode == 'video-only' or mode == 'audio-video':
            temp = add_video_noise(file, SNR)
        output = split(temp)
        for i in output:
            result[file].append(convert(i, mode))
    return result


def add_noise(signal, SNR):
    """
    adds noise to video data
    :param signal (np.ndarray): original signal
    :param SNR (float): SNR in dB
    :return (np.ndarray): resulting output
    """
    if SNR >= 100:
        return signal
    noise = np.ndarray(signal.shape, np.uint8)
    channel_num = 1 if len(signal.shape) == 2 else len(signal.shape)
    a = tuple((0 for i in range(channel_num)))
    b = tuple((255 * ((100 - SNR) / 100) for i in range(channel_num)))
    cv.randn(noise, a, b)
    return signal + noise


def add_video_noise(filepath, SNR):
    """
    video noise driver
    :param filepath (str): filepath
    :param SNR (float): SNR in dB
    :return (str): output filepath
    """
    if SNR >= 100:
        return filepath
    output = filepath.split('.')
    output[-2] += '_noisy_' + str(SNR)
    output = '.'.join(output).split('\\')[-1]
    output = 'temp/' + output
    output = os.path.abspath(output)
    check_audio, check_video = check_streams(filepath)
    if check_audio:
        get_audio(filepath, 'temp/temp_audio.mp4')
    cam = cv.VideoCapture(filepath)
    fps = cam.get(cv.CAP_PROP_FPS)
    recorder = cv.VideoWriter('temp/temp_video.mp4', cv.VideoWriter_fourcc('m', 'p', '4', 'v'), fps,
                              (int(cam.get(3)), int(cam.get(4))))
    pos_frame = cam.get(cv.CAP_PROP_POS_FRAMES)
    while True:
        ret, frame = cam.read()
        if ret:
            noisy_frame = add_noise(frame, SNR)
            recorder.write(noisy_frame)
            pos_frame = cam.get(cv.CAP_PROP_POS_FRAMES)
        else:
            if cam.get(cv.CAP_PROP_POS_FRAMES) == cam.get(cv.CAP_PROP_FRAME_COUNT):
                # If the number of captured frames is equal to the total number of frames,
                # we stop
                break
            else:
                cam.set(cv.CAP_PROP_POS_FRAMES, pos_frame - 1)
                cv.waitKey(100)
    cam.release()
    recorder.release()
    if check_audio:
        merge('temp/temp_video.mp4', 'temp/temp_audio.mp4', output)
    else:
        shutil.copyfile('temp/temp_video.mp4', output)
    return output


def generate_audio_noise(dir_path):
    """
    generates audio noise
    :param dir_path (str): path to directory with data
    :return (void):
    """
    from scipy.io import wavfile
    files = [os.path.abspath(dir_path + '/' + file) for file in os.listdir(dir_path)]
    noise = np.empty((0))
    while len(noise) < 16000 * 3600:
        noisePart = np.zeros(16000 * 60)
        indices = np.random.randint(0, len(files), 20)
        for ix in indices:
            sampFreq, audio = wavfile.read(files[ix])
            audio = audio / np.max(np.abs(audio))
            pos = np.random.randint(0, abs(len(audio) - len(noisePart)) + 1)
            if len(audio) > len(noisePart):
                noisePart = noisePart + audio[pos:pos + len(noisePart)]
            else:
                noisePart = noisePart[pos:pos + len(audio)] + audio
        noise = np.concatenate([noise, noisePart], axis=0)
    noise = noise[:16000 * 3600]
    noise = (noise / 20) * 32767
    noise = np.floor(noise).astype(np.int16)
    wavfile.write(dir_path + "/noise.wav", 16000, noise)


def get_from_file(file, param):
    """
        gets the value of the specified parameter in the provided file
        :param file (str): filepath
        :param param (str): file parameter
        :return (dict(str:str)): param value
    """
    search_string = str(param)
    result = dict()
    with open(file) as f:
        file_content = f.readlines()
        for line in file_content:
            if search_string in line:
                temp = line.split(':')
                result[temp[0].strip()] = temp[1].strip()
    return result


def change_file(file, param, param_val):
    """
    changes the value of the specified parameter in the provided file to the desired
    :param file (str): filepath
    :param param (str): file parameter
    :param param_val (str): desired parameter value
    :return (bool): whether a change has been made
    """
    status = False
    search_string = str(param)
    new_file_content = None
    with open(file) as f:
        file_content = f.readlines()
        new_lines = []
        for line in file_content:
            if search_string in line:
                status = True
                comment_pos = line.find('#')
                comment_str = ''
                if comment_pos != -1:
                    comment_str = line[comment_pos:]
                line = search_string + f' : {param_val}  {comment_str}'
            new_lines.append(line.strip())
        new_file_content = '\n'.join(new_lines)
    if new_file_content is not None:
        with open(file, 'w') as f:
            f.write(new_file_content)
    return status


def change_config_file(mode, param, param_val):
    """
    changes the value of the specified parameter in the provided file to the desired
    :param mode (str): a string indicating the file type
    :param param (str): file parameter
    :param param_val (str): desired parameter value
    :return (bool): whether a change has been made
    """
    status = False
    if mode == 'audio-only':
        file = 'other/deep_avsr/audio_only/config.py'
    elif mode == 'video-only':
        file = 'other/deep_avsr/video_only/config.py'
    else:
        file = 'other/deep_avsr/audio_visual/config.py'
    search_string_1 = f"args['{param}']"
    search_string_2 = f'args["{param}"]'
    new_file_content = None
    with open(file) as f:
        file_content = f.readlines()
        new_lines = []
        for line in file_content:
            if search_string_1 in line or search_string_2 in line:
                status = True
                search_string = search_string_1
                comment_pos = line.find('#')
                comment_str = ''
                if comment_pos != -1:
                    comment_str = line[comment_pos:]
                if type(param_val) == str:
                    param_val = f"'{param_val}'"
                line = search_string + f' = {param_val}  {comment_str}'
            new_lines.append(line)
        new_file_content = ''.join(new_lines)
    if new_file_content is not None:
        with open(file, 'w') as f:
            f.write(new_file_content)
    return status


def main():
    parser = ArgumentParser()
    parser.add_argument('path', type=str, help='file absolute path')
    parser.add_argument('-o', action='store_true', help='overwrite current file')
    args = parser.parse_args()
    output = convert(args.path, args.o)
    split(output, args.o)
    print('done')


if __name__ == '__main__':
    print(change_config_file('audio-only', 'NOISE_SNR_DB', 10))
    print(change_config_file('audio-only', 'NOISE_SNR_DB', 20))
    print('done')
