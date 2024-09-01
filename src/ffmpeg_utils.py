import subprocess
import os
import requests
import zipfile
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import re
from utils import convert_time_to_seconds

def check_ffmpeg():
    try:
        subprocess.run(['ffmpeg', '-version'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    ffmpeg_path = os.path.join(os.getcwd(), 'data', 'ffmpeg', 'bin', 'ffmpeg.exe')
    if os.path.isfile(ffmpeg_path):
        os.environ["PATH"] += os.pathsep + os.path.join(os.getcwd(), 'data', 'ffmpeg', 'bin')
        return True

    return False

def download_ffmpeg(progress_var, progress_label, root):
    url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    local_zip_path = "ffmpeg.zip"
    extract_path = "data"

    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    downloaded_size = 0

    with open(local_zip_path, 'wb') as file:
        for chunk in response.iter_content(chunk_size=8192):
            file.write(chunk)
            downloaded_size += len(chunk)

            # 使用 root.after 在主线程中更新 Tkinter 组件
            root.after(0, lambda: progress_var.set(downloaded_size / total_size * 100))
            root.after(0, lambda: progress_label.config(text=f"下载进度: {downloaded_size / total_size * 100:.2f}%"))

    # 使用 root.after 更新完成状态
    root.after(0, lambda: progress_label.config(text="下载完成，正在解压..."))

    with zipfile.ZipFile(local_zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_path)

    extracted_dir_name = None
    with zipfile.ZipFile(local_zip_path, 'r') as zip_ref:
        extracted_dir_name = zip_ref.namelist()[0].split('/')[0]

    if extracted_dir_name:
        os.rename(os.path.join(extract_path, extracted_dir_name), os.path.join(extract_path, 'ffmpeg'))

    os.environ["PATH"] += os.pathsep + os.path.join(extract_path, 'ffmpeg', 'bin')
    os.remove(local_zip_path)

    # 使用 root.after 关闭窗口
    root.after(0, root.destroy)

def start_download(progress_var, progress_label, root):
    download_thread = threading.Thread(target=download_ffmpeg, args=(progress_var, progress_label, root))
    download_thread.start()

def start_ffmpeg_download():
    root = tk.Tk()
    root.title("FFmpeg 安装器")
    root.geometry("400x150")

    progress_var = tk.DoubleVar()
    progress_bar = ttk.Progressbar(root, variable=progress_var, maximum=100)
    progress_bar.pack(pady=20)

    progress_label = tk.Label(root, text="FFmpeg 未安装，正在下载...", font=("Helvetica", 10))
    progress_label.pack(pady=10)

    root.update_idletasks()
    start_download(progress_var, progress_label, root)

    root.mainloop()

def run_ffmpeg_command_with_progress(command, progress_var, progress_bar, progress_label, root, total_duration=None):
    # 输出执行的命令
    command_with_quotes = [
        f'"{arg}"' if ' ' in arg else arg for arg in command
    ]
    print("Executing command:", " ".join(command_with_quotes))

    try:
        # 重置进度条和进度变量
        progress_var.set("进度: 0%")
        progress_bar["value"] = 0
        progress_bar["maximum"] = 100
        progress_label.grid()  # 显示进度标签
        progress_bar.grid()  # 显示进度条

        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        time_pattern = re.compile(r"time=(\d+:\d+:\d+\.\d+)")
        duration_pattern = re.compile(r"Duration: (\d+:\d+:\d+\.\d+)")

        def update_progress(current_time, total_duration, current_seconds, total_seconds):
            progress_var.set(f"进度: {current_time} / {total_duration}")
            progress_bar["value"] = current_seconds
            progress_bar["maximum"] = total_seconds

        if total_duration:
            total_seconds = convert_time_to_seconds(total_duration)
            root.after(0, update_progress, "00:00:00.00", total_duration, 0, total_seconds)
        else:
            total_seconds = None

        while True:
            output = process.stderr.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                # 解析总时长
                if total_seconds is None:
                    duration_match = duration_pattern.search(output)
                    if duration_match:
                        total_duration = duration_match.group(1)
                        total_seconds = convert_time_to_seconds(total_duration)
                        root.after(0, update_progress, "00:00:00.00", total_duration, 0, total_seconds)

                # 解析进度信息
                time_match = time_pattern.search(output)
                if time_match:
                    current_time = time_match.group(1)
                    current_seconds = convert_time_to_seconds(current_time)
                    if total_seconds:
                        progress_percentage = (current_seconds / total_seconds) * 100
                        root.after(0, update_progress, current_time, total_duration, progress_percentage, 100)

        return process.poll()
    except Exception as e:
        return f"执行命令时出错: {e}"

def show_ffmpeg_info():
    command = ['ffmpeg', '-version']
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    messagebox.showinfo("FFmpeg信息", result.stdout)

def generate_command(input_file, format, resolution, video_bitrate, audio_bitrate, quality, custom_width, custom_height, rotate, keep_metadata, start_time, end_time, quick_trim):
    # 获取输入文件的扩展名
    input_format = os.path.splitext(input_file)[1][1:]

    # 处理“原格式”选项
    if format.startswith("原格式"):
        format = input_format

    # 处理编码器选项
    codec = None
    if format == "mp4 (h264)":
        format = "mp4"
        codec = "libx264"
    elif format == "mp4 (h265)":
        format = "mp4"
        codec = "libx265"

    # 处理自定义分辨率
    if resolution == "与原视频相同":
        resolution = None
    elif resolution == "自定义":
        resolution = f"{custom_width}x{custom_height}"

    output_file = filedialog.asksaveasfilename(
        title="保存文件",
        defaultextension=f".{format}",
        filetypes=[(f"{format.upper()} 文件", f"*.{format}"), ("所有文件", "*.*")]
    )
    if output_file:
        command = [
            'ffmpeg', '-y', '-i', input_file,
            '-map_metadata', '0' if keep_metadata else '-1'
        ]

        if keep_metadata and input_format == "mov":
            command.extend(['-movflags', 'use_metadata_tags'])

        if codec:
            command.extend(['-c:v', codec])
        if resolution:
            command.extend(['-s', resolution])
        if video_bitrate and video_bitrate != 'kbps':
            command.extend(['-b:v', f'{video_bitrate}k'])
        if audio_bitrate and audio_bitrate != 'kbps':
            command.extend(['-b:a', f'{audio_bitrate}k'])
        if quality:
            command.extend(['-crf', str(quality)])
        if rotate != '不旋转':
            if rotate == '顺时针旋转90°':
                command.extend(['-vf', 'transpose=1'])
            elif rotate == '逆时针旋转90°':
                command.extend(['-vf', 'transpose=2'])
            elif rotate == '旋转180°':
                command.extend(['-vf', 'transpose=2,transpose=2'])
            elif rotate == '水平翻转':
                command.extend(['-vf', 'hflip'])
            elif rotate == '垂直翻转':
                command.extend(['-vf', 'vflip'])

        if start_time and end_time:
            command.extend(['-ss', start_time, '-to', end_time])
            if quick_trim:
                command.extend(['-c:v', 'copy', '-c:a', 'copy'])

        command.append(output_file)

        return command
    return None