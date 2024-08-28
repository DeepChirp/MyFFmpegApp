from tkinter import *
from ffmpeg_utils import check_ffmpeg, start_ffmpeg_download
from gui import show_main_window, set_root

def main():
    if not check_ffmpeg():
        start_ffmpeg_download()  # 下载FFmpeg

    root = Tk()
    root.title("视频&音频处理器")
    root.geometry("500x400")

    set_root(root)  # 设置GUI的根窗口
    show_main_window()  # 调用主窗口显示函数
    root.mainloop()

if __name__ == "__main__":
    main()