import subprocess


command =
ffmpeg = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE )
out, err = ffmpeg.communicate(frames.tostring() )

