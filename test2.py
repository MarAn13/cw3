import pyaudio
import wave

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
RECORD_SECONDS = 5
WAVE_OUTPUT_FILENAME = "test1.wav"

p = pyaudio.PyAudio()
# Learn what your OS+Hardware can do
defaultCapability = p.get_default_host_api_info()
print(defaultCapability)

# See if you can make it do what you want
isSupported = p.is_format_supported(input_format=pyaudio.paInt8, input_channels=1, rate=22050, input_device=0)
print(isSupported)
info = p.get_host_api_info_by_index(0)
numdevices = info.get('deviceCount')
for i in range(0, numdevices):
    if (p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
        print("Input Device id ", i, " - ", p.get_device_info_by_host_api_device_index(0, i).get('name'))
print(p.get_default_input_device_info())
exit()
stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK)

print("* recording")

frames = []

for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
    data = stream.read(CHUNK)
    frames.append(data)

print("* done recording")
if p:
    print('y -0')
else:
    print('n -0')
stream.stop_stream()
stream.close()
p.terminate()
if p:
    print('y -1')
else:
    print('n -1')

wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
wf.setnchannels(CHANNELS)
wf.setsampwidth(p.get_sample_size(FORMAT))
wf.setframerate(RATE)
wf.writeframes(b''.join(frames))
wf.close()