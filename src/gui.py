import os
import threading
import tkinter as tk
import json
from tkinter import ttk, StringVar, Label, IntVar, Frame, messagebox, filedialog, BooleanVar, Toplevel, Canvas, Menu
from file_operations import import_files
from ffmpeg_utils import show_ffmpeg_info, run_ffmpeg_command_with_progress, generate_command
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
def add_placeholder(entry, placeholder, disable_placeholder=False):
    entry_style = ttk.Style()

    def set_placeholder():
        entry.insert(0, placeholder)
        entry_style.configure("Placeholder.TEntry", foreground='grey')
        entry.configure(style="Placeholder.TEntry")

    def remove_placeholder():
        entry.delete(0, "end")
        entry_style.configure("TEntry", foreground='black')
        entry.configure(style="TEntry")

    def on_focus_in(event):
        if entry.get() == placeholder:
            remove_placeholder()

    def on_focus_out(event):
        if entry.get() == "":
            set_placeholder()

    if not disable_placeholder:
        set_placeholder()
        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)
    else:
        entry_style.configure("TEntry", foreground='black')
        entry.configure(style="TEntry")

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
    title_label = ttk.Label(root, text="视频&音频处理器", font=("SimSun", 16, "bold"))
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

    # 预设按钮
    preset_button = ttk.Button(root, text="预设", command=lambda: show_preset_window(), width=20)
    preset_button.grid(row=4, column=0, columnspan=2, pady=10)

    # 版权信息和FFmpeg信息
    footer_frame = ttk.Frame(root)
    footer_frame.grid(row=5, column=0, columnspan=2, pady=20, sticky="s")

    footer_label = ttk.Label(footer_frame, text="© 2024 视频处理器", font=("SimSun", 10), foreground="gray")
    footer_label.pack(side="left")

    separator_label = ttk.Label(footer_frame, text=" | ", font=("SimSun", 10), foreground="gray")
    separator_label.pack(side="left")

    ffmpeg_info_label = ttk.Label(footer_frame, text="查看FFmpeg信息", font=("SimSun", 10, "underline"), foreground="gray", cursor="hand2")
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
        title_label = Label(root, text="导出选项", font=("SimSun", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=10, sticky="ew")

        # 格式选项
        format_label = Label(root, text="格式:")
        format_label.grid(row=1, column=0, padx=5, pady=5, sticky="e")
        CreateToolTip(format_label, text="视频编码的方式，不同设备及软件对各种格式的支持不同")
        format_var = StringVar(root)
        format_var.set(f"原格式 ({input_format})")
        format_options = [f"原格式 ({input_format})", "mp4 (h264)", "mp4 (h265)", "avi", "mkv", "mov", "flv", "webm"]
        format_menu = ttk.Combobox(root, textvariable=format_var, values=format_options, state="readonly")
        format_menu.config(width=15)  # 设置下拉框宽度
        format_menu.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        # 分辨率选项
        resolution_label = Label(root, text="分辨率:")
        resolution_label.grid(row=2, column=0, padx=5, pady=5, sticky="e")
        CreateToolTip(resolution_label, text="视频图像的大小，即水平和垂直像素数")
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
                add_placeholder(custom_height_entry, "高度", disable_placeholder=True)

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
                add_placeholder(custom_width_entry, "宽度", disable_placeholder=True)

        resolution_var.trace("w", toggle_custom_resolution)
        custom_width_entry.bind("<Return>", update_height)
        custom_height_entry.bind("<Return>", update_width)
        add_placeholder(custom_width_entry, "宽度")
        add_placeholder(custom_height_entry, "高度")

        # 初始隐藏自定义分辨率输入框容器
        custom_resolution_frame.grid_remove()

        # 音频码率选项
        audio_label = Label(root, text="音频码率:")
        audio_label.grid(row=4, column=0, padx=5, pady=5, sticky="e")
        CreateToolTip(audio_label, text="音频数据传输速率，影响音频的质量")
        audio_bitrate_var = StringVar(root)
        audio_bitrate_var.set("")
        audio_bitrate_entry = ttk.Entry(root, textvariable=audio_bitrate_var, width=18)  # 调整输入框宽度
        audio_bitrate_entry.grid(row=4, column=1, padx=5, pady=5, sticky="w")
        add_placeholder(audio_bitrate_entry, "kbps")

        # 品质选项
        quality_label = Label(root, text="视频品质:")
        quality_label.grid(row=5, column=0, padx=5, pady=5, sticky="e")
        CreateToolTip(quality_label, text="视频压缩质量，值越大质量越高，但文件大小也越大")
        quality_var = IntVar(root)
        quality_var.set(28)  # 默认值
        quality_scale = ttk.Scale(root, from_=0, to=51, orient="horizontal", variable=quality_var, length=150)
        quality_scale.grid(row=5, column=1, padx=5, pady=5, sticky="w")

        default_quality_button = ttk.Button(root, text="默认值", command=lambda: quality_var.set(28))
        default_quality_button.grid(row=5, column=2, padx=5, pady=5, sticky="w")
        CreateToolTip(default_quality_button, text="点击恢复默认值")

        # 旋转选项
        rotate_label = Label(root, text="旋转:")
        rotate_label.grid(row=6, column=0, padx=5, pady=5, sticky="e")
        CreateToolTip(rotate_label, text="旋转视频的角度")
        rotate_var = StringVar(root)
        rotate_var.set("不旋转")  # 默认值
        rotate_options = ["不旋转", "顺时针旋转90°", "逆时针旋转90°", "旋转180°", "水平翻转", "垂直翻转"]
        rotate_menu = ttk.Combobox(root, textvariable=rotate_var, values=rotate_options, state="readonly")
        rotate_menu.config(width=15)  # 设置下拉框宽度
        rotate_menu.grid(row=6, column=1, padx=5, pady=5, sticky="w")

        # TODO: 添加无损旋转选项，仅修改旋转播放信息而不重新编码

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

        export_button = ttk.Button(button_frame, text="导出", command=lambda: start_export_thread(generate_command(input_file, format_var.get(), resolution_var.get(), None, audio_bitrate_var.get(), 51 - quality_var.get(), custom_width_var.get(), custom_height_var.get(), rotate_var.get(), metadata_var.get(), None, None, False), export_button, back_button, progress_bar, progress_var, progress_label, root))
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
        title_label = Label(root, text="导出选项", font=("SimSun", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=10, sticky="ew")

        # 格式选项
        formar_label = Label(root, text="格式:")
        formar_label.grid(row=1, column=0, padx=5, pady=5, sticky="e")
        CreateToolTip(formar_label, text="音频编码的方式，不同设备及软件对各种格式的支持不同")
        format_var = StringVar(root)
        format_var.set(f"原格式 ({input_format})")
        format_options = [f"原格式 ({input_format})", "mp3", "wav", "flac", "aac", "ogg"]
        format_menu = ttk.Combobox(root, textvariable=format_var, values=format_options, state="readonly")
        format_menu.config(width=15)  # 设置下拉框宽度
        format_menu.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        # 音频码率选项
        audio_label = Label(root, text="音频码率:")
        audio_label.grid(row=2, column=0, padx=5, pady=5, sticky="e")
        CreateToolTip(audio_label, text="音频数据传输速率，影响音频的质量")
        audio_bitrate_var = StringVar(root)
        audio_bitrate_var.set("")
        audio_bitrate_entry = ttk.Entry(root, textvariable=audio_bitrate_var, width=18)  # 设置输入框宽度
        audio_bitrate_entry.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        add_placeholder(audio_bitrate_entry, "kbps")

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

        export_button = ttk.Button(button_frame, text="导出", command=lambda: start_export_thread(generate_command(input_file, format_var.get(), None, None, audio_bitrate_var.get(), None, None, None, None, metadata_var.get(), None, None, None), export_button, back_button, progress_bar, progress_var, progress_label, root))
        export_button.grid(row=0, column=1, padx=5)

        # 进度条
        progress_var = StringVar()
        progress_var.set("进度: 0%")
        progress_label = Label(root, textvariable=progress_var)
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
        # 标题
        title_label = Label(root, text="裁剪选项", font=("SimSun", 16, "bold"))
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
        quick_trim_checkbox = ttk.Checkbutton(root, text="快速裁剪（可能导致开头和结尾的帧不准确）", variable=quick_trim_var)
        quick_trim_checkbox.grid(row=3, column=0, columnspan=3, pady=5)
        CreateToolTip(quick_trim_checkbox, text="勾选后，视频将不重新编码，裁剪速度更快，但关键帧可能不准确")

        # 导出和返回按钮
        button_frame = ttk.Frame(root)
        button_frame.grid(row=4, column=0, columnspan=3, pady=10)

        back_button = ttk.Button(button_frame, text="返回", command=show_main_window)
        back_button.grid(row=0, column=0, padx=5)

        export_button = ttk.Button(button_frame, text="导出", command=lambda: start_export_thread(generate_command(input_file, "原格式", None, None, None, None, None, None, None, True, start_time_var.get(), end_time_var.get(), quick_trim_var.get()), export_button, back_button, progress_bar, progress_var, progress_label, root, convert_seconds_to_time(convert_time_to_seconds(end_time_var.get()) - convert_time_to_seconds(start_time_var.get()))))
        export_button.grid(row=0, column=1, padx=5)

        # 进度条
        progress_var = StringVar()
        progress_var.set("进度: 0%")
        progress_label = Label(root, textvariable=progress_var)
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

def show_preset_window():
    # 确保 data 目录存在
    data_dir = "data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    # 确保 presets.json 文件存在
    preset_file = os.path.join(data_dir, "presets.json")
    if not os.path.exists(preset_file):
        with open(preset_file, 'w', encoding='utf-8') as f:
            json.dump([], f)

    # 读取预设文件
    with open(preset_file, 'r', encoding='utf-8') as f:
        presets = json.load(f)

    # 按照 key 排序预设
    presets.sort(key=lambda x: x["key"])

    # 创建预设管理窗口
    preset_window = Toplevel(root)
    preset_window.title("预设管理")

    # 显示预设的表格
    columns = ("命令", "描述", "输出格式")
    tree = ttk.Treeview(preset_window, columns=columns, show="headings")
    for col in columns:
        tree.heading(col, text=col)
    for preset in presets:
        command_str = ' '.join(preset["command"])  # 将命令列表转换为字符串
        output_type_display = "与导入格式相同" if preset["output_type"] == "keep" else preset["output_type"]
        tree.insert("", "end", iid=preset["key"], values=(command_str, preset["description"], output_type_display))
    tree.grid(row=0, column=0, columnspan=4, padx=10, pady=10)

    # 添加、修改、删除按钮
    add_button = ttk.Button(preset_window, text="添加", command=lambda: add_preset(preset_window, tree, presets, preset_file))
    add_button.grid(row=1, column=0, padx=5, pady=5)
    edit_button = ttk.Button(preset_window, text="修改", command=lambda: edit_preset(preset_window, tree, presets, preset_file))
    edit_button.grid(row=1, column=1, padx=5, pady=5)
    delete_button = ttk.Button(preset_window, text="删除", command=lambda: delete_preset(tree, presets, preset_file))
    delete_button.grid(row=1, column=2, padx=5, pady=5)
    run_button = ttk.Button(preset_window, text="运行", command=lambda: run_preset(tree))
    run_button.grid(row=1, column=3, padx=5, pady=5)

    # 创建右键菜单
    def show_context_menu(event):
        context_menu.post(event.x_root, event.y_root)

    context_menu = Menu(preset_window, tearoff=0)
    context_menu.add_command(label="上移", command=lambda: move_preset(tree, presets, preset_file, -1))
    context_menu.add_command(label="下移", command=lambda: move_preset(tree, presets, preset_file, 1))

    tree.bind("<Button-3>", show_context_menu)

    def move_preset(tree, presets, preset_file, direction):
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showwarning("警告", "请选择一个预设进行移动")
            return

        selected_item = selected_item[0]
        index = next((i for i, preset in enumerate(presets) if preset["key"] == int(selected_item)), None)
        if index is None:
            return

        new_index = index + direction
        if new_index < 0 or new_index >= len(presets):
            return

        # 交换预设位置
        presets[index], presets[new_index] = presets[new_index], presets[index]

        # 更新 key 值以反映新的顺序
        for i, preset in enumerate(presets):
            preset["key"] = i + 1

        # 重新保存 JSON 文件
        with open(preset_file, 'w', encoding='utf-8') as f:
            json.dump(presets, f, ensure_ascii=False, indent=4)

        # 重新加载 Treeview
        tree.delete(*tree.get_children())
        for preset in presets:
            command_str = ' '.join(preset["command"])  # 将命令列表转换为字符串
            output_type_display = "与导入格式相同" if preset["output_type"] == "keep" else preset["output_type"]
            tree.insert("", "end", iid=preset["key"], values=(command_str, preset["description"], output_type_display))

    def add_preset(preset_window, tree, presets, preset_file):
        def save_preset():
            updated_output_type = output_type_var.get()
            if updated_output_type == "与导入格式相同":
                updated_output_type = "keep"

            new_preset = {
                "key": max(preset["key"] for preset in presets) + 1 if presets else 1,
                "command": command_var.get().split(),  # 将命令字符串转换为列表
                "description": description_var.get(),
                "output_type": updated_output_type
            }
            presets.append(new_preset)
            with open(preset_file, 'w', encoding='utf-8') as f:
                json.dump(presets, f, ensure_ascii=False, indent=4)

            command_str = ' '.join(new_preset["command"])  # 将命令列表转换为字符串
            output_type_display = "与导入格式相同" if new_preset["output_type"] == "keep" else new_preset["output_type"]
            tree.insert("", "end", iid=new_preset["key"], values=(command_str, new_preset["description"], output_type_display))
            add_window.destroy()

        add_window = Toplevel(preset_window)
        add_window.title("添加预设")

        command_var = StringVar()
        description_var = StringVar()
        output_type_var = StringVar()

        ttk.Label(add_window, text="命令:").grid(row=0, column=0, padx=5, pady=5)
        ttk.Entry(add_window, textvariable=command_var).grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(add_window, text="描述:").grid(row=1, column=0, padx=5, pady=5)
        ttk.Entry(add_window, textvariable=description_var).grid(row=1, column=1, padx=5, pady=5)
        ttk.Label(add_window, text="输出格式:").grid(row=2, column=0, padx=5, pady=5)
        ttk.Entry(add_window, textvariable=output_type_var).grid(row=2, column=1, padx=5, pady=5)

        save_button = ttk.Button(add_window, text="保存", command=save_preset)
        save_button.grid(row=3, column=0, columnspan=2, padx=5, pady=5)

    def edit_preset(preset_window, tree, presets, preset_file):
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showwarning("警告", "请选择一个预设进行修改")
            return

        selected_item = selected_item[0]
        selected_preset = tree.item(selected_item, "values")

        def save_preset():
            updated_output_type = output_type_var.get()
            if updated_output_type == "与导入格式相同":
                updated_output_type = "keep"

            updated_preset = {
                "key": int(selected_item),
                "command": command_var.get().split(),  # 将命令字符串转换为列表
                "description": description_var.get(),
                "output_type": updated_output_type
            }
            for i, preset in enumerate(presets):
                if preset["key"] == int(selected_item):
                    presets[i] = updated_preset
                    break
            with open(preset_file, 'w', encoding='utf-8') as f:
                json.dump(presets, f, ensure_ascii=False, indent=4)

            # 更新 Treeview 中的项，而不是删除旧项并插入新项
            command_str = ' '.join(updated_preset["command"])  # 将命令列表转换为字符串
            output_type_display = "与导入格式相同" if updated_preset["output_type"] == "keep" else updated_preset["output_type"]
            tree.item(selected_item, values=(command_str, updated_preset["description"], output_type_display))
            edit_window.destroy()

        edit_window = Toplevel(preset_window)
        edit_window.title("修改预设")

        command_var = StringVar(value=' '.join(selected_preset[0].split()))  # 将命令字符串转换为列表再转换为字符串
        description_var = StringVar(value=selected_preset[1])
        output_type_display = "与导入格式相同" if selected_preset[2] == "keep" else selected_preset[2]
        output_type_var = StringVar(value=output_type_display)

        ttk.Label(edit_window, text="命令:").grid(row=0, column=0, padx=5, pady=5)
        ttk.Entry(edit_window, textvariable=command_var).grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(edit_window, text="描述:").grid(row=1, column=0, padx=5, pady=5)
        ttk.Entry(edit_window, textvariable=description_var).grid(row=1, column=1, padx=5, pady=5)
        ttk.Label(edit_window, text="输出格式:").grid(row=2, column=0, padx=5, pady=5)
        ttk.Entry(edit_window, textvariable=output_type_var).grid(row=2, column=1, padx=5, pady=5)

        save_button = ttk.Button(edit_window, text="保存", command=save_preset)
        save_button.grid(row=3, column=0, columnspan=2, padx=5, pady=5)

    def delete_preset(tree, presets, preset_file):
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showwarning("警告", "请选择一个预设进行删除")
            return

        selected_item = selected_item[0]
        selected_key = int(selected_item)

        # 在 presets 列表中查找具有相同 key 的项并删除
        for i, preset in enumerate(presets):
            if preset["key"] == selected_key:
                del presets[i]
                break

        # 更新剩余预设的 key 值
        for i, preset in enumerate(presets):
            preset["key"] = i + 1

        # 更新 Treeview 和预设文件
        tree.delete(selected_item)
        with open(preset_file, 'w', encoding='utf-8') as f:
            json.dump(presets, f, ensure_ascii=False, indent=4)

        # 重新加载 Treeview
        tree.delete(*tree.get_children())
        for preset in presets:
            command_str = ' '.join(preset["command"])  # 将命令列表转换为字符串
            output_type_display = "与导入格式相同" if preset["output_type"] == "keep" else preset["output_type"]
            tree.insert("", "end", iid=preset["key"], values=(command_str, preset["description"], output_type_display))

    def run_preset(tree):
        selected_item = tree.selection()[0]
        selected_preset = tree.item(selected_item, "values")

        # 调整索引，假设 key 列不可见
        command = selected_preset[0].split()  # 将命令字符串转换为列表
        output_type = selected_preset[2]

        # 解析命令中的文件类型
        file_types = []
        placeholders = ["[视频]", "[音频]", "[媒体]", "[字幕]"]
        for placeholder in placeholders:
            for cmd in command:
                if placeholder in cmd:
                    file_types.append(placeholder.strip("[]"))

        def execute_command(file_paths, command):
            # 替换命令中的文件占位符
            for i, file_path in enumerate(file_paths):
                command = [cmd.replace(f"[{file_types[i]}]", file_path, 1) for cmd in command]

            # 如果 output_type 是 keep，则使用输入文件的扩展名
            if output_type == "keep":
                input_file_extension = os.path.splitext(file_paths[0])[1]
                output_extension = input_file_extension
            else:
                output_extension = f".{output_type}"

            # 让用户指定输出文件名
            output_file = filedialog.asksaveasfilename(
                title="保存文件",
                defaultextension=output_extension,
                filetypes=[(f"{output_extension.upper()} 文件", f"*{output_extension}"), ("所有文件", "*.*")]
            )
            if output_file:
                command = [cmd.replace("[输出]", output_file) for cmd in command]

                # 创建新窗口
                progress_window = Toplevel(root)
                progress_window.title("进度")

                # 显示进度条和进度标签
                progress_var = StringVar()
                progress_bar = ttk.Progressbar(progress_window, orient="horizontal", length=300, mode="determinate")
                progress_bar.grid(pady=10)
                progress_label = Label(progress_window, textvariable=progress_var)
                progress_label.grid(pady=5)

                def run_and_update():
                    result = run_ffmpeg_command_with_progress(command, progress_var, progress_bar, progress_label, progress_window, None)
                    messagebox.showinfo("结果", f"完成，返回码: {result}")
                    progress_window.destroy()

                # 启动线程
                merge_thread = threading.Thread(target=run_and_update)
                merge_thread.start()

        import_files(len(file_types), file_types, lambda file_paths: execute_command(file_paths, command))

def start_export_thread(command, export_button, back_button, progress_bar, progress_var, progress_label, root, total_duration=None):
    if not command:
        return

    # 隐藏导出按钮，显示进度条和进度标签
    export_button.grid_remove()
    back_button.grid_remove()
    progress_bar.grid()
    progress_label.grid()
    progress_var.set("进度: 0%")

    def export_and_update():
        # 运行FFmpeg命令并显示进度
        result = run_ffmpeg_command_with_progress(command, progress_var, progress_bar, progress_label, root, total_duration)

        # 显示导出结果
        messagebox.showinfo("导出结果", f"完成，返回码: {result}")

        # 显示导出按钮，隐藏进度条和进度标签
        root.after(0, export_button.grid)
        root.after(0, back_button.grid)
        root.after(0, progress_bar.grid_remove)
        root.after(0, progress_label.grid_remove)

    # 启动导出线程
    export_thread = threading.Thread(target=export_and_update)
    export_thread.start()