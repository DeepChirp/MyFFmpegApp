import os
import threading
import tkinter as tk
from tkinter import ttk, StringVar, Label, OptionMenu, Button, Entry, Scale, IntVar, Frame, messagebox, filedialog, BooleanVar, Checkbutton, Toplevel, Canvas
from file_operations import import_files, export_file
from ffmpeg_utils import show_ffmpeg_info, run_ffmpeg_command_with_progress
from utils import get_media_duration, get_aspect_ratio, convert_time_to_seconds, convert_seconds_to_time

# 全局变量 root
root = None

class CreateToolTip(object):
    """
    create a tooltip for a given widget
    reference: https://stackoverflow.com/questions/3221956/how-do-i-display-tooltips-in-tkinter
    """
    def __init__(self, widget, text='widget info'):
        self.waittime = 500     # 毫秒
        self.wraplength = 180   # 像素
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<ButtonPress>", self.leave)
        self.id = None
        self.tw = None

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.waittime, self.showtip)

    def unschedule(self):
        id = self.id
        self.id = None
        if id:
            self.widget.after_cancel(id)

    def showtip(self, event=None):
        x = y = 0
        x, y, cx, cy = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        # 创建一个顶级窗口
        self.tw = tk.Toplevel(self.widget)
        # 仅保留标签并移除应用窗口
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(self.tw, text=self.text, justify='left',
                       background="#ffffff", relief='solid', borderwidth=1,
                       wraplength=self.wraplength)
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tw
        self.tw = None
        if tw:
            tw.destroy()

# 提示文本功能
def add_placeholder(entry, placeholder):
    entry.insert(0, placeholder)
    entry_style = ttk.Style()
    entry_style.configure("Placeholder.TEntry", foreground='grey')
    entry.configure(style="Placeholder.TEntry")

    def on_focus_in(event):
        if entry.get() == placeholder:
            entry.delete(0, "end")
            entry_style.configure("TEntry", foreground='black')
            entry.configure(style="TEntry")

    def on_focus_out(event):
        if entry.get() == "":
            entry.insert(0, placeholder)
            entry_style.configure("Placeholder.TEntry", foreground='grey')
            entry.configure(style="Placeholder.TEntry")

    entry.bind("<FocusIn>", on_focus_in)
    entry.bind("<FocusOut>", on_focus_out)

def set_root(tk_root):
    global root
    root = tk_root

def clear_layout():
    # 移除所有子控件
    for widget in root.winfo_children():
        widget.destroy()

    # 清除列和行的配置
    for i in range(10):  # 假设最多有10行和列
        root.columnconfigure(i, weight=0)
        root.rowconfigure(i, weight=0)

def show_main_window():
    # 清理之前的布局配置
    clear_layout()

    # 标题
    title_label = ttk.Label(root, text="视频&音频处理器", font=("Helvetica", 16, "bold"))
    title_label.grid(row=0, column=0, columnspan=2, pady=20)

    # 导入视频按钮
    import_video_button = ttk.Button(root, text="导入视频", command=lambda: import_files(1, ["视频"], export_video_window), width=20)
    import_video_button.grid(row=1, column=0, columnspan=2, pady=10)

    # 导入音频按钮
    import_audio_button = ttk.Button(root, text="导入音频", command=lambda: import_files(1, ["音频"], export_audio_window), width=20)
    import_audio_button.grid(row=2, column=0, columnspan=2, pady=10)

    # 裁剪视频或音频按钮
    trim_media_button = ttk.Button(root, text="裁剪视频或音频", command=lambda: import_files(1, ["媒体"], trim_media_window), width=20)
    trim_media_button.grid(row=3, column=0, columnspan=2, pady=10)

    # 合并视频与音频按钮
    merge_video_audio_button = ttk.Button(root, text="合并视频与音频", command=lambda: import_files(2, ["视频", "音频"], merge_audio_video), width=20)
    merge_video_audio_button.grid(row=4, column=0, columnspan=2, pady=10)

    # 版权信息和FFmpeg信息
    footer_frame = ttk.Frame(root)
    footer_frame.grid(row=5, column=0, columnspan=2, pady=20, sticky="s")

    footer_label = ttk.Label(footer_frame, text="© 2024 视频处理器", font=("Helvetica", 10), foreground="gray")
    footer_label.pack(side="left")

    separator_label = ttk.Label(footer_frame, text=" | ", font=("Helvetica", 10), foreground="gray")
    separator_label.pack(side="left")

    ffmpeg_info_label = ttk.Label(footer_frame, text="查看FFmpeg信息", font=("Helvetica", 10, "underline"), foreground="gray", cursor="hand2")
    ffmpeg_info_label.pack(side="left")
    ffmpeg_info_label.bind("<Button-1>", lambda e: show_ffmpeg_info())

    # 配置列和行的权重，使其在窗口大小改变时自动调整
    for i in range(2):
        root.columnconfigure(i, weight=1)
    for i in range(6):
        root.rowconfigure(i, weight=1)

def export_video_window(file_paths):
    # 清理之前的布局配置
    clear_layout()

    # 处理每个文件路径
    for input_file in file_paths:
        # 获取输入文件的扩展名和分辨率
        input_format = os.path.splitext(input_file)[1][1:]
        aspect_ratio = get_aspect_ratio(input_file)

        # 标题
        title_label = Label(root, text="导出选项", font=("Helvetica", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=10, sticky="ew")

        # 格式选项
        Label(root, text="格式:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        format_var = StringVar(root)
        format_var.set(f"原格式 ({input_format})")
        format_options = [f"原格式 ({input_format})", "mp4 (h264)", "mp4 (h265)", "avi", "mkv", "mov", "flv", "webm"]
        format_menu = ttk.Combobox(root, textvariable=format_var, values=format_options, state="readonly")
        format_menu.config(width=15)  # 设置下拉框宽度
        format_menu.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        # 分辨率选项
        Label(root, text="分辨率:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        resolution_var = StringVar(root)
        resolution_var.set("与原视频相同")
        resolution_options = ["与原视频相同"]  # 添加默认选项
        if aspect_ratio == "4:3":
            resolution_options += ["640x480", "800x600", "1024x768", "自定义"]
        elif aspect_ratio == "16:9":
            resolution_options += ["1280x720", "1920x1080", "2560x1440", "自定义"]
        else:
            resolution_options += ["自定义"]  # 默认选项
        resolution_menu = ttk.Combobox(root, textvariable=resolution_var, values=resolution_options, state="readonly")
        resolution_menu.config(width=15)  # 设置下拉框宽度
        resolution_menu.grid(row=2, column=1, padx=5, pady=5, sticky="w")

        # 自定义分辨率输入框容器
        custom_resolution_frame = Frame(root)
        custom_width_var = StringVar(root)
        custom_height_var = StringVar(root)
        custom_width_entry = ttk.Entry(custom_resolution_frame, textvariable=custom_width_var, width=8)  # 调整输入框宽度
        custom_height_entry = ttk.Entry(custom_resolution_frame, textvariable=custom_height_var, width=8)  # 调整输入框宽度

        custom_width_entry.grid(row=0, column=0, padx=(5, 2), pady=5, sticky="w")
        custom_height_entry.grid(row=0, column=1, padx=(2, 5), pady=5, sticky="w")

        def toggle_custom_resolution(*args):
            if resolution_var.get() == "自定义":
                custom_resolution_frame.grid(row=3, column=1, columnspan=2, padx=5, pady=5, sticky="w")
            else:
                custom_resolution_frame.grid_remove()

        def update_height(event=None):
            if custom_width_var.get().isdigit():
                width = int(custom_width_var.get())
                if aspect_ratio == "4:3":
                    height = int(width * 3 / 4)
                elif aspect_ratio == "16:9":
                    height = int(width * 9 / 16)
                else:
                    height = int(width * aspect_ratio.split(":")[1] / aspect_ratio.split(":")[0])  # 默认
                custom_height_var.set(str(height))

        def update_width(event=None):
            if custom_height_var.get().isdigit():
                height = int(custom_height_var.get())
                if aspect_ratio == "4:3":
                    width = int(height * 4 / 3)
                elif aspect_ratio == "16:9":
                    width = int(height * 16 / 9)
                else:
                    width = int(height * aspect_ratio.split(":")[0] / aspect_ratio.split(":")[1])  # 默认
                custom_width_var.set(str(width))

        resolution_var.trace("w", toggle_custom_resolution)
        custom_width_entry.bind("<Return>", update_height)
        custom_height_entry.bind("<Return>", update_width)

        # 初始隐藏自定义分辨率输入框容器
        custom_resolution_frame.grid_remove()

        # 视频码率选项
        Label(root, text="视频码率:").grid(row=4, column=0, padx=5, pady=5, sticky="e")
        video_bitrate_var = StringVar(root)
        video_bitrate_var.set("")
        video_bitrate_entry = ttk.Entry(root, textvariable=video_bitrate_var, width=18)  # 调整输入框宽度
        video_bitrate_entry.grid(row=4, column=1, padx=5, pady=5, sticky="w")

        # 音频码率选项
        Label(root, text="音频码率:").grid(row=5, column=0, padx=5, pady=5, sticky="e")
        audio_bitrate_var = StringVar(root)
        audio_bitrate_var.set("")
        audio_bitrate_entry = ttk.Entry(root, textvariable=audio_bitrate_var, width=18)  # 调整输入框宽度
        audio_bitrate_entry.grid(row=5, column=1, padx=5, pady=5, sticky="w")

        add_placeholder(video_bitrate_entry, "kbps")
        add_placeholder(audio_bitrate_entry, "kbps")
        add_placeholder(custom_width_entry, "宽度")
        add_placeholder(custom_height_entry, "高度")

        # 质量选项
        Label(root, text="质量").grid(row=6, column=0, padx=5, pady=5, sticky="e")
        quality_var = IntVar(root)
        quality_var.set(28)  # 默认值
        quality_scale = ttk.Scale(root, from_=0, to=51, orient="horizontal", variable=quality_var, length=150)
        quality_scale.grid(row=6, column=1, padx=5, pady=5, sticky="w")

        default_quality_button = ttk.Button(root, text="默认值", command=lambda: quality_var.set(28))
        default_quality_button.grid(row=6, column=2, padx=5, pady=5, sticky="w")
        CreateToolTip(default_quality_button, text="点击恢复默认值")

        # 保留元数据复选框
        metadata_var = BooleanVar()
        metadata_var.set(True)
        metadata_checkbutton = ttk.Checkbutton(root, text=" 保留元数据", variable=metadata_var)
        metadata_checkbutton.grid(row=7, column=1, columnspan=2, padx=5, pady=5, sticky="w")

        # 导出和返回按钮
        button_frame = Frame(root)
        button_frame.grid(row=8, column=0, columnspan=3, pady=10)

        back_button = ttk.Button(button_frame, text="返回", command=show_main_window)
        back_button.grid(row=0, column=0, padx=5)

        export_button = ttk.Button(button_frame, text="导出", command=lambda: start_export_thread(input_file, format_var.get(), resolution_var.get(), video_bitrate_var.get(), audio_bitrate_var.get(), 51 - quality_var.get(), export_button, back_button, progress_bar, progress_var, progress_label, custom_width_var.get(), custom_height_var.get(), metadata_var.get(), None, None, False, root))
        export_button.grid(row=0, column=1, padx=5)

        # 进度条
        progress_var = StringVar()
        progress_var.set("进度: 0%")
        progress_label = Label(root, textvariable=progress_var)
        progress_label.grid(row=8, column=0, columnspan=3, pady=5, sticky="ew")
        progress_label.grid_remove()  # 初始隐藏进度标签
        progress_bar = ttk.Progressbar(root, orient="horizontal", length=200, mode="determinate")
        progress_bar.grid(row=9, column=0, columnspan=3, pady=5, sticky="ew")
        progress_bar.grid_remove()  # 初始隐藏进度条

        # 配置列和行的权重，使其在窗口大小改变时自动调整
        for i in range(3):
            root.columnconfigure(i, weight=1)
        for i in range(9):
            root.rowconfigure(i, weight=1)

def export_audio_window(file_paths):
    # 清理之前的布局配置
    clear_layout()

    # 处理每个文件路径
    for input_file in file_paths:
        # 获取输入文件的扩展名
        input_format = os.path.splitext(input_file)[1][1:]

        # 标题
        title_label = ttk.Label(root, text="导出选项", font=("Helvetica", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=10, sticky="ew")

        # 格式选项
        ttk.Label(root, text="格式:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        format_var = StringVar(root)
        format_var.set(f"原格式 ({input_format})")
        format_options = [f"原格式 ({input_format})", "mp3", "wav", "flac", "aac", "ogg"]
        format_menu = ttk.Combobox(root, textvariable=format_var, values=format_options, state="readonly")
        format_menu.config(width=10)  # 设置下拉框宽度
        format_menu.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        # 音频码率选项
        ttk.Label(root, text="音频码率 (kbps):").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        audio_bitrate_var = StringVar(root)
        audio_bitrate_var.set("")
        audio_bitrate_entry = ttk.Entry(root, textvariable=audio_bitrate_var, width=10)
        audio_bitrate_entry.grid(row=2, column=1, padx=5, pady=5, sticky="w")

        # 保留元数据复选框
        metadata_var = BooleanVar()
        metadata_var.set(True)
        metadata_checkbutton = ttk.Checkbutton(root, text=" 保留元数据", variable=metadata_var)
        metadata_checkbutton.grid(row=3, column=1, columnspan=2, padx=5, pady=5, sticky="w")

        # 导出和返回按钮
        button_frame = ttk.Frame(root)
        button_frame.grid(row=4, column=0, columnspan=3, pady=10)

        back_button = ttk.Button(button_frame, text="返回", command=show_main_window)
        back_button.grid(row=0, column=0, padx=5)

        export_button = ttk.Button(button_frame, text="导出", command=lambda: start_export_thread(input_file, format_var.get(), None, None, audio_bitrate_var.get(), None, export_button, back_button, progress_bar, progress_var, progress_label, None, None, metadata_var.get(), None, None, False, root))
        export_button.grid(row=0, column=1, padx=5)

        # 进度条
        progress_var = StringVar()
        progress_var.set("进度: 0%")
        progress_label = ttk.Label(root, textvariable=progress_var)
        progress_label.grid(row=4, column=0, columnspan=3, pady=5, sticky="ew")
        progress_label.grid_remove()  # 初始隐藏进度标签
        progress_bar = ttk.Progressbar(root, orient="horizontal", length=200, mode="determinate")
        progress_bar.grid(row=5, column=0, columnspan=3, pady=5, sticky="ew")
        progress_bar.grid_remove()  # 初始隐藏进度条

        # 配置列和行的权重，使其在窗口大小改变时自动调整
        for i in range(3):
            root.columnconfigure(i, weight=1)
        for i in range(6):
            root.rowconfigure(i, weight=1)

def trim_media_window(file_paths):
    # 清理之前的布局配置
    clear_layout()

    # 处理每个文件路径
    for input_file in file_paths:
        # 获取输入文件的扩展名
        input_format = os.path.splitext(input_file)[1][1:]

        # 标题
        title_label = ttk.Label(root, text="裁剪选项", font=("Helvetica", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=10, sticky="ew")

        # 获取媒体文件的总时长
        total_duration = get_media_duration(input_file)
        total_seconds = convert_time_to_seconds(total_duration)

        # 开始时间和结束时间变量
        start_time_var = StringVar(root)
        end_time_var = StringVar(root)

        # 设置初始值
        start_time_var.set("00:00:00.00")
        end_time_var.set(total_duration)

        # 实时预览滑动条
        scale_frame = ttk.Frame(root)
        scale_frame.grid(row=1, column=0, columnspan=3, pady=10, sticky="ew")

        canvas = Canvas(scale_frame, height=50)
        canvas.pack(fill="both", expand=True)

        # 初始滑杆位置
        start_pos = 50
        end_pos = 550

        # 绘制滑动条和滑杆
        line = canvas.create_line(start_pos, 25, end_pos, 25, fill="black", width=2)
        start_slider = canvas.create_rectangle(start_pos-5, 15, start_pos+5, 35, fill="blue")
        end_slider = canvas.create_rectangle(end_pos-5, 15, end_pos+5, 35, fill="red")

        def move_slider(event):
            nonlocal start_pos, end_pos
            x = event.x
            total_length = canvas.winfo_width() - 100  # 滑动条的总长度
            if abs(x - start_pos) < abs(x - end_pos):
                start_pos = max(50, min(x, canvas.winfo_width() - 50))
                canvas.coords(start_slider, start_pos-5, 15, start_pos+5, 35)
                start_time_var.set(convert_seconds_to_time((start_pos - 50) / total_length * total_seconds))
            else:
                end_pos = min(canvas.winfo_width() - 50, max(x, 50))
                canvas.coords(end_slider, end_pos-5, 15, end_pos+5, 35)
                end_time_var.set(convert_seconds_to_time((end_pos - 50) / total_length * total_seconds))
            canvas.coords(line, 50, 25, canvas.winfo_width() - 50, 25)

        canvas.bind("<B1-Motion>", move_slider)

        def resize(event):
            nonlocal start_pos, end_pos
            canvas.coords(line, 50, 25, event.width - 50, 25)
            end_pos = event.width - 50
            canvas.coords(end_slider, end_pos-5, 15, end_pos+5, 35)
            canvas.coords(start_slider, start_pos-5, 15, start_pos+5, 35)

        canvas.bind("<Configure>", resize)

        # 显示开始时间和结束时间
        time_frame = ttk.Frame(root)
        time_frame.grid(row=2, column=0, columnspan=3, pady=10, sticky="ew")

        start_time_label = ttk.Label(time_frame, textvariable=start_time_var)
        start_time_label.pack(side="left", padx=10)
        end_time_label = ttk.Label(time_frame, textvariable=end_time_var)
        end_time_label.pack(side="right", padx=10)

        # 快速裁剪复选框
        quick_trim_var = BooleanVar()
        quick_trim_checkbox = ttk.Checkbutton(root, text="快速裁剪（开头和结尾的部分帧可能会出现问题）", variable=quick_trim_var)
        quick_trim_checkbox.grid(row=3, column=0, columnspan=3, pady=5)

        # 导出和返回按钮
        button_frame = ttk.Frame(root)
        button_frame.grid(row=4, column=0, columnspan=3, pady=10)

        back_button = ttk.Button(button_frame, text="返回", command=show_main_window)
        back_button.grid(row=0, column=0, padx=5)

        export_button = ttk.Button(button_frame, text="导出", command=lambda: start_export_thread(input_file, "不转换", None, None, None, None, export_button, back_button, progress_bar, progress_var, progress_label, None, None, quick_trim_var.get(), start_time_var.get(), end_time_var.get(), quick_trim_var.get(), root))
        export_button.grid(row=0, column=1, padx=5)

        # 进度条
        progress_var = StringVar()
        progress_var.set("进度: 0%")
        progress_label = ttk.Label(root, textvariable=progress_var)
        progress_label.grid(row=4, column=0, columnspan=3, pady=5, sticky="ew")
        progress_label.grid_remove()  # 初始隐藏进度标签
        progress_bar = ttk.Progressbar(root, orient="horizontal", length=200, mode="determinate")
        progress_bar.grid(row=5, column=0, columnspan=3, pady=5, sticky="ew")
        progress_bar.grid_remove()  # 初始隐藏进度条

        # 配置列和行的权重，使其在窗口大小改变时自动调整
        for i in range(3):
            root.columnconfigure(i, weight=1)
        for i in range(6):
            root.rowconfigure(i, weight=1)

def merge_audio_video(file_paths):
    if len(file_paths) != 2:
        messagebox.showerror("错误", "需要选择一个视频文件和一个音频文件")
        return
    video_file, audio_file = file_paths

    output_file = filedialog.asksaveasfilename(
        title="保存合并文件",
        defaultextension=".mp4",
        filetypes=[("MP4 文件", "*.mp4"), ("所有文件", "*.*")]
    )
    if output_file:
        # 获取视频和音频的总时长
        video_duration = get_media_duration(video_file)
        audio_duration = get_media_duration(audio_file)
        if not video_duration or not audio_duration:
            messagebox.showerror("错误", "无法获取视频或音频的时长")
            return

        # 取较短的总时长
        total_duration = min(video_duration, audio_duration, key=convert_time_to_seconds)

        command = ['ffmpeg', '-i', video_file, '-i', audio_file, '-c:v', 'copy', '-c:a', 'copy', output_file]

        # 创建新窗口
        progress_window = Toplevel(root)
        progress_window.title("合并进度")

        # 显示进度条和进度标签
        progress_var = StringVar()
        progress_bar = ttk.Progressbar(progress_window, orient="horizontal", length=300, mode="determinate")
        progress_bar.grid(pady=10)
        progress_label = Label(progress_window, textvariable=progress_var)
        progress_label.grid(pady=5)

        def merge_and_update():
            result = run_ffmpeg_command_with_progress(command, progress_var, progress_bar, progress_label, progress_window, None, total_duration)
            messagebox.showinfo("合并结果", f"合并完成，返回码: {result}")
            progress_window.destroy()

        # 启动合并线程
        merge_thread = threading.Thread(target=merge_and_update)
        merge_thread.start()

def start_export_thread(input_file, format, resolution, video_bitrate, audio_bitrate, quality, export_button, back_button, progress_bar, progress_var, progress_label, custom_width, custom_height, keep_metadata, start_time, end_time, quick_trim, root):
    # 隐藏导出按钮，显示进度条和进度标签
    export_button.grid_remove()
    back_button.grid_remove()
    progress_bar.grid()
    progress_label.grid()
    progress_var.set("进度: 0%")

    def export_and_update():
        export_file(input_file, format, resolution, video_bitrate, audio_bitrate, quality, progress_bar, progress_var, progress_label, custom_width, custom_height, keep_metadata, start_time, end_time, quick_trim, root)
        # 显示导出按钮，隐藏进度条和进度标签
        root.after(0, export_button.grid)
        root.after(0, back_button.grid)
        root.after(0, progress_bar.grid_remove)
        root.after(0, progress_label.grid_remove)

    # 启动导出线程
    export_thread = threading.Thread(target=export_and_update)
    export_thread.start()