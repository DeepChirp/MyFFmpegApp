from tkinter import filedialog, messagebox
import os
from ffmpeg_utils import run_ffmpeg_command_with_progress
from utils import convert_time_to_seconds, convert_seconds_to_time

def import_files(file_count, file_types, command):
    """
    导入指定数量的文件，并执行指定的命令。

    :param file_count: 需要导入的文件数量
    :param file_types: 文件类型列表，格式为["视频", "音频", "媒体", "字幕"]
    :param command: 选择文件完成后执行的命令，参数为选择的文件路径列表
    """
    # 定义常见的文件类型及其扩展名
    extensions = {
        "视频": [("视频文件", "*.mp4;*.avi;*.mkv;*.mov;*.flv;*.ogg;*.webm")],
        "音频": [("音频文件", "*.mp3;*.aac;*.wav;*.flac;*.ogg;*.m4a")],
        "媒体": [("媒体文件", "*.mp4;*.avi;*.mkv;*.mov;*.flv;*.ogg;*.webm;*.mp3;*.aac;*.wav;*.flac;*.m4a")],
        "字幕": [("字幕文件", "*.srt;*.ssa;*.sub;*.pgs")]
    }

    file_paths = []
    for i in range(file_count):
        file_type = file_types[i]
        if file_type not in extensions:
            messagebox.showerror("文件导入", f"未知的文件类型: {file_type}")
            return

        file_path = filedialog.askopenfilename(
            title=f"选择{file_type}文件",
            filetypes=extensions[file_type] + [("所有文件", "*.*")]
        )
        if file_path:
            file_paths.append(file_path)
        else:
            messagebox.showwarning("文件导入", f"未选择{file_type}文件")
            return

    messagebox.showinfo("文件导入", f"已选择文件: {', '.join(file_paths)}")
    command(file_paths)

def export_file(input_file, format, resolution, video_bitrate, audio_bitrate, quality, progress_bar, progress_var, progress_label, custom_width, custom_height, keep_metadata, start_time, end_time, quick_trim, root):
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

    total_duration = None

    output_file = filedialog.asksaveasfilename(
        title="保存文件",
        defaultextension=f".{format}",
        filetypes=[(f"{format.upper()} 文件", f"*.{format}"), ("所有文件", "*.*")]
    )
    if output_file:
        command = ['ffmpeg', '-y', '-i', input_file]
        if keep_metadata:
            command.append('-map_metadata')
            command.append('0')
            if input_format == "mov":
                command.append('-movflags')
                command.append('use_metadata_tags')
        else:
            command.append('-map_metadata')
            command.append('-1')
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
        if start_time and end_time:
            command.extend(['-ss', start_time, '-to', end_time])
            if quick_trim:
                command.extend(['-c:v', 'copy', '-c:a', 'copy'])
            total_duration = convert_seconds_to_time(convert_time_to_seconds(end_time) - convert_time_to_seconds(start_time))
        command.append(output_file)

        # 输出执行的命令
        print("Executing command:", " ".join(command))

        # 运行FFmpeg命令并显示进度
        result = run_ffmpeg_command_with_progress(command, progress_var, progress_bar, progress_label, root, start_time, total_duration)

        # 显示导出结果
        messagebox.showinfo("导出结果", f"完成，返回码: {result}")