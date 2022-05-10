## Requirements
    ffmpeg-python
    python==3.6.9
    editdistance==0.5.3
    matplotlib==3.1.1
    numpy==1.18.1
    scipy==1.3.1
    tqdm==4.42.1
    pytorch==1.2.0
    opencv-python==4.2.0
    pandas
    openpyxl
    python-docx
    pyaudio
    pydub

## Neural network setup guide
### forked from https://github.com/lordmartian/deep_avsr
    place pre-trained weights of AO, VO, AV models in 'code/other/deep_avsr/../final/models' directory for the corresponding NN model
    place visual frontend and language model in 'code/other/weights/' named visual_frontend.pt and language_model.pt

## Launch application via code/main.py file
