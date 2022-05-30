"""
Author: Smeet Shah
Copyright (c) 2020 Smeet Shah
File part of 'deep_avsr' GitHub repository available at -
https://github.com/lordmartian/deep_avsr
"""

import os


def preprocess_sample(input, output):
    """
    Function to preprocess each data sample.
    Extracts the audio from the video file using the FFmpeg utility and saves it to a wav file.
    """
    videoFile = input
    audioFile = output
    v2aCommand = "ffmpeg -y -v quiet -i " + videoFile + " -ac 1 -ar 16000 -vn " + audioFile
    os.system(v2aCommand)
    return


def preprocess_dir(dir_path):
    for file in os.listdir(dir_path):
        filename = dir_path + '\\' + file
        output = filename.split('.')[0] + '.wav'
        preprocess_sample(filename, output)


if __name__ == '__main__':
    preprocess_dir(r'C:\Users\marem\PycharmProjects\home\projects\cw3\app\code\data_processed')
