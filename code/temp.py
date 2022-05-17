import numpy as np
import cv2 as cv
import acoustics


def add_noise1(signal, SNR):
    if SNR >= 100:
        return signal
    noise = np.ndarray(signal.shape, np.uint8)
    channel_num = 1 if len(signal.shape) == 2 else len(signal.shape)
    a = tuple((0 for i in range(channel_num)))
    b = tuple((255 * ((100 - SNR) / 100) for i in range(channel_num)))
    cv.randn(noise, a, b)
    return signal + noise


def add_noise2(signal, snr):
    signal = signal
    # Generate the noise as you did
    noise = acoustics.generator.white(signal.size).reshape(*signal.shape)
    # For the record I think np.random.random does exactly the same thing

    # work out the current SNR
    current_snr = np.mean(signal) / np.std(noise)
    snr = 10.0 ** (snr / 10.0)
    print(current_snr, snr)

    # scale the noise by the snr ratios (smaller noise <=> larger snr)
    noise *= (current_snr / snr)

    # return the new signal with noise
    return signal + noise


def add_noise3(signal, SNR):
    row, col, ch = signal.shape
    mean = 0
    sigma = 255 * ((100 - SNR) / 100)
    gauss = np.random.normal(mean, sigma, (row, col, ch))
    gauss = gauss.reshape(row, col, ch)
    noisy = signal + gauss
    return noisy


def add_noise4(signal, SNR):
    img = cv.imread(signal, 0) / 255
    noise = np.random.normal(loc=0, scale=1, size=img.shape)

    # noise overlaid over image
    # noisy = np.clip((img + noise * 0.2), 0, 1)
    noisy2 = np.clip((img + noise * ((100 - SNR) / 100)), 0, 1)
    return noisy2


def add_noise(signal, SNR):
    signal = signal / 255
    mean = 0
    std_dev = (100 - SNR) / 100
    noise = np.random.normal(loc=mean, scale=std_dev, size=signal.shape)
    return signal + noise


# cap = cv.VideoCapture(0)
# if not cap.isOpened():
#     print("Cannot open camera")
#     exit()
# while True:
# Capture frame-by-frame
# ret, frame = cap.read()
# frame = cv.flip(frame, 1)
# frame = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
# frame = cv.imread(r'C:\Users\marem\OneDrive\Desktop\test.jpg', 1)
# cap = cv.VideoCapture(r'C:\Users\marem\PycharmProjects\home\projects\cw3\app\code\other\demo\audio-video\test5.mp4')
# ret, frame = cap.read()
# frame = r'C:\Users\marem\OneDrive\Desktop\test.jpg'
# if frame is read correctly ret is True
# if not ret:
#     print("Can't receive frame (stream end?). Exiting ...")
#     break
# Our operations on the frame come here
# Display the resulting frame
# noise1 = add_noise(frame, 0)
# noise2 = add_noise(frame, 10)
# noise3 = add_noise(frame, 20)
# noise4 = add_noise(frame, 30)
# noise5 = add_noise(frame, 40)
# noise6 = add_noise(frame, 50)
# noise7 = add_noise(frame, 60)
# noise8 = add_noise(frame, 70)
# noise9 = add_noise(frame, 80)
# noise10 = add_noise(frame, 90)
# noise11 = add_noise(frame, 100)
# cv.imshow('SNR 0', noise1)
# cv.imshow('SNR 10', noise2)
# cv.imshow('SNR 20', noise3)
# cv.imshow('SNR 30', noise4)
# cv.imshow('SNR 40', noise5)
# cv.imshow('SNR 50', noise6)
# cv.imshow('SNR 60', noise7)
# cv.imshow('SNR 70', noise8)
# cv.imshow('SNR 80', noise9)
# cv.imshow('SNR 90', noise10)
# cv.imshow('SNR 100', noise11)
# cv.waitKey(0)
# if cv.waitKey(1) == ord('q'):
#     break
# When everything done, release the capture
# cap.release()
# cv.destroyAllWindows()
def add_video_noise(filepath, output, SNR):
    from utils import merge, get_audio
    get_audio(filepath, 'temp_audio.mp4')
    cam = cv.VideoCapture(filepath)
    fps = cam.get(cv.CAP_PROP_FPS)
    recorder = cv.VideoWriter('temp_video.mp4', cv.VideoWriter_fourcc('m', 'p', '4', 'v'), fps,
                              (int(cam.get(3)), int(cam.get(4))))
    pos_frame = cam.get(cv.CAP_PROP_POS_FRAMES)
    while True:
        ret, frame = cam.read()
        if ret:
            noisy_frame = add_noise1(frame, SNR)
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
    merge('temp_video.mp4', 'temp_audio.mp4', output)
    print('done')


def test():
    cam = cv.VideoCapture(r'C:\Users\marem\PycharmProjects\home\projects\cw3\app\code\other\demo\audio-video\test5.mp4')
    fps = cam.get(cv.CAP_PROP_FPS)
    recorder = cv.VideoWriter(r'C:\Users\marem\PycharmProjects\home\projects\cw3\app\code\other\demo\audio-video\test5_noisy_first.mp4', cv.VideoWriter_fourcc('m', 'p', '4', 'v'), fps,
                              (int(cam.get(3)), int(cam.get(4))))
    pos_frame = cam.get(cv.CAP_PROP_POS_FRAMES)
    while True:
        ret, frame = cam.read()
        if ret:
            noisy_frame = add_noise(frame, 80)
            cv.imshow('frame', frame)
            cv.imshow('noisy frame', noisy_frame)
            recorder.write(noisy_frame)
            pos_frame = cam.get(cv.CAP_PROP_POS_FRAMES)
            cv.waitKey(100)
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
    print('done')


for i in range(0, 11):
    add_video_noise(r'C:\Users\marem\PycharmProjects\home\projects\cw3\app\code\other\demo\audio-video\test5.mp4', f'C:\\Users\\marem\\PycharmProjects\\home\\projects\\cw3\\app\\code\\other\\demo\\audio-video\\test5_noisy_0_{i}.mp4', i * 10)

# test()
