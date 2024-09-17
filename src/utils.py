import subprocess
import re


def get_media_duration(file_path):
    command = ["ffmpeg", "-i", file_path]
    result = subprocess.run(command, stderr=subprocess.PIPE, text=True)
    duration_pattern = re.compile(r"Duration: (\d+:\d+:\d+\.\d+)")
    match = duration_pattern.search(result.stderr)
    if match:
        return match.group(1)
    return None


# 获取视频宽高比，以便提供分辨率选项
def get_aspect_ratio(file_path):
    command = ["ffmpeg", "-i", file_path]
    result = subprocess.run(
        command, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True
    )
    resolution_pattern = re.compile(r"(\d{2,5})x(\d{2,5})")
    match = resolution_pattern.search(result.stderr)
    if match:
        width, height = map(int, match.groups())
        ratio = width / height
        if abs(ratio - 4 / 3) < 0.01:
            return "4:3"
        elif abs(ratio - 16 / 9) < 0.01:
            return "16:9"
        else:
            return "Other"
    return None


def convert_time_to_seconds(time_str):
    h, m, s = map(float, time_str.split(":"))
    return int(h * 3600 + m * 60 + s)


def convert_seconds_to_time(seconds):
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{int(h):02}:{int(m):02}:{s:05.2f}"
