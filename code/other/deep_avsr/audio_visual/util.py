import torch
import numpy as np
import os

from scipy.io import wavfile

from .models.av_net import AVNet
from .models.lrs2_char_lm import LRS2CharLM
from .models.visual_frontend import VisualFrontend
from .data.utils import prepare_main_input, collate_fn
from .utils.preprocessing import preprocess_sample
from .utils.decoders import ctc_greedy_decode, ctc_search_decode
from .utils.metrics import compute_wer

from argparse import ArgumentParser


def predict(files):
    # files {file: [filepath, filepath]}
    from importlib import reload
    from . import config
    reload(config)
    print('av lm decoder noise db: ', config.args["TEST_DEMO_MODE"], config.args["USE_LM"], config.args["TEST_DEMO_DECODING"], config.args["TEST_DEMO_NOISY"], config.args["NOISE_SNR_DB"])
    result = dict()
    np.random.seed(config.args["SEED"])
    torch.manual_seed(config.args["SEED"])
    gpuAvailable = torch.cuda.is_available()
    device = torch.device("cuda" if gpuAvailable else "cpu")

    if config.args["TRAINED_MODEL_FILE"] is not None:
        # declaring the model and loading the trained weights
        model = AVNet(config.args["TX_NUM_FEATURES"], config.args["TX_ATTENTION_HEADS"], config.args["TX_NUM_LAYERS"], config.args["PE_MAX_LENGTH"],
                      config.args["AUDIO_FEATURE_SIZE"], config.args["TX_FEEDFORWARD_DIM"], config.args["TX_DROPOUT"], config.args["NUM_CLASSES"])
        model.load_state_dict(torch.load(config.args["CODE_DIRECTORY"] + config.args["TRAINED_MODEL_FILE"], map_location=device))
        model.to(device)

        # declaring the visual frontend module
        vf = VisualFrontend()
        vf.load_state_dict(torch.load(config.args["TRAINED_FRONTEND_FILE"], map_location=device))
        vf.to(device)

        # declaring the language model
        lm = LRS2CharLM()
        lm.load_state_dict(torch.load(config.args["TRAINED_LM_FILE"], map_location=device))
        lm.to(device)
        if not config.args["USE_LM"]:
            lm = None

        # reading the noise file
        if config.args["TEST_DEMO_NOISY"]:
            _, noise = wavfile.read(config.args["DATA_DIRECTORY"] + '\\' + "noise.wav")
        else:
            noise = None

        # walking through the demo directory and running the model on all video files in it
        for filepath, file_chunks in files.items():
            result[filepath] = ''
            for file in file_chunks:
                if file.endswith(".mp4"):
                    file_output = config.args['PRED_OUTPUT'] + 'temp'

                    # preprocessing the sample
                    params = {"roiSize": config.args["ROI_SIZE"], "normMean": config.args["NORMALIZATION_MEAN"],
                              "normStd": config.args["NORMALIZATION_STD"], "vf": vf}
                    preprocess_sample(file, file_output, params)

                    # converting the data sample into appropriate tensors for input to the model
                    audioFile = file_output + ".wav"
                    visualFeaturesFile = file_output + ".npy"
                    audioParams = {"stftWindow": config.args["STFT_WINDOW"], "stftWinLen": config.args["STFT_WIN_LENGTH"],
                                   "stftOverlap": config.args["STFT_OVERLAP"]}
                    videoParams = {"videoFPS": config.args["VIDEO_FPS"]}
                    inp, _, inpLen, _ = prepare_main_input(audioFile, visualFeaturesFile, None, noise,
                                                           config.args["MAIN_REQ_INPUT_LENGTH"],
                                                           config.args["CHAR_TO_INDEX"], config.args["NOISE_SNR_DB"], audioParams,
                                                           videoParams)
                    inputBatch, _, inputLenBatch, _ = collate_fn([(inp, None, inpLen, None)])

                    # running the model
                    inputBatch = ((inputBatch[0].float()).to(device), (inputBatch[1].float()).to(device))
                    inputLenBatch = (inputLenBatch.int()).to(device)
                    if config.args["TEST_DEMO_MODE"] == "AO":
                        inputBatch = (inputBatch[0], None)
                    elif config.args["TEST_DEMO_MODE"] == "VO":
                        inputBatch = (None, inputBatch[1])
                    elif config.args["TEST_DEMO_MODE"] == "AV":
                        pass
                    else:
                        exit()

                    model.eval()
                    with torch.no_grad():
                        outputBatch = model(inputBatch)

                    # obtaining the prediction using CTC deocder
                    if config.args["TEST_DEMO_DECODING"] == "greedy":
                        predictionBatch, predictionLenBatch = ctc_greedy_decode(outputBatch, inputLenBatch,
                                                                                config.args["CHAR_TO_INDEX"]["<EOS>"])

                    elif config.args["TEST_DEMO_DECODING"] == "search":
                        beamSearchParams = {"beamWidth": config.args["BEAM_WIDTH"], "alpha": config.args["LM_WEIGHT_ALPHA"],
                                            "beta": config.args["LENGTH_PENALTY_BETA"],
                                            "threshProb": config.args["THRESH_PROBABILITY"]}
                        predictionBatch, predictionLenBatch = ctc_search_decode(outputBatch, inputLenBatch,
                                                                                beamSearchParams,
                                                                                config.args["CHAR_TO_INDEX"][" "],
                                                                                config.args["CHAR_TO_INDEX"]["<EOS>"], lm)
                    else:
                        exit()

                    # converting character indices back to characters
                    pred = predictionBatch[:][:-1]
                    pred = "".join([config.args["INDEX_TO_CHAR"][ix] for ix in pred.tolist()])

                    if result[filepath] != '':
                        result[filepath] += ' '
                    result[filepath] += pred
    return result


def main():
    parser = ArgumentParser()
    parser.add_argument('path', type=str, nargs='?', help='file with target info absolute path')
    args = parser.parse_args()
    if args.path is not None:
        target = dict()
        with open(args.path) as f:
            lines = f.readlines()
            for line in lines:
                data = line.split(':')
                target[data[0].strip()] = data[1].strip()
        print(predict(target))
    else:
        print(predict(['C:\\Users\\marem\\PycharmProjects\\home\\projects\\cw3\\app\\other\\demo\\audio-video\\test5.mp4']))


if __name__ == "__main__":
    main()
