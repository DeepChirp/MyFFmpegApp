from tkinter import filedialog, messagebox


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
        "媒体": [
            (
                "媒体文件",
                "*.mp4;*.avi;*.mkv;*.mov;*.flv;*.ogg;*.webm;*.mp3;*.aac;*.wav;*.flac;*.m4a",
            )
        ],
        "字幕": [("字幕文件", "*.srt;*.ssa;*.sub;*.pgs")],
    }

    file_paths = []
    for i in range(file_count):
        file_type = file_types[i]
        if file_type not in extensions:
            messagebox.showerror("文件导入", f"未知的文件类型: {file_type}")
            return

        file_path = filedialog.askopenfilename(
            title=f"选择{file_type}文件",
            filetypes=extensions[file_type] + [("所有文件", "*.*")],
        )
        if file_path:
            file_paths.append(file_path)
        else:
            messagebox.showwarning("文件导入", f"未选择{file_type}文件")
            return

    messagebox.showinfo("文件导入", f"已选择文件: {', '.join(file_paths)}")
    command(file_paths)
