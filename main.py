import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import subprocess
import threading
import os
import time

class VideoCompressorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🎬 Video Compressor")
        self.root.geometry("600x350")
        self.root.configure(bg="#2e2e2e")

        # --- Language setup ---
        self.languages = {
            "en": {
                "choose_file": "Choose video file to compress",
                "btn_choose": "📂 Choose File",
                "preset": "Preset (speed/compression):",
                "btn_compress": "⚡ Compress Video",
                "status_done": "✅ Done!",
                "msg_done": "Video successfully compressed!",
                "compressing": "Compressing..."
            },
            "ru": {
                "choose_file": "Выберите видеофайл для сжатия",
                "btn_choose": "📂 Выбрать файл",
                "preset": "Пресет (скорость/сжатие):",
                "btn_compress": "⚡ Сжать видео",
                "status_done": "✅ Готово!",
                "msg_done": "Видео успешно сжато!",
                "compressing": "Идёт сжатие..."
            }
        }
        self.current_lang = "en"

        # --- Fonts and Styles ---
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TButton", font=("Segoe UI", 12), padding=8, background="#4CAF50")
        style.configure("TLabel", font=("Segoe UI", 11), background="#2e2e2e", foreground="white")
        style.configure("Horizontal.TProgressbar", thickness=25)

        # --- Interface ---
        self.label = ttk.Label(root, text=self.languages[self.current_lang]["choose_file"])
        self.label.pack(pady=10)

        self.choose_btn = ttk.Button(root, text=self.languages[self.current_lang]["btn_choose"], command=self.choose_file)
        self.choose_btn.pack(pady=5)

        # Presets
        self.preset_label = ttk.Label(root, text=self.languages[self.current_lang]["preset"])
        self.preset_label.pack(pady=5)

        self.preset_var = tk.StringVar(value="medium")
        self.preset_menu = ttk.Combobox(root, textvariable=self.preset_var,
                                        values=["ultrafast", "superfast", "veryfast", "faster",
                                                "fast", "medium", "slow", "slower", "veryslow"],
                                        state="readonly", font=("Segoe UI", 11))
        self.preset_menu.pack(pady=5)

        self.compress_btn = ttk.Button(root, text=self.languages[self.current_lang]["btn_compress"],
                                       command=self.start_compression, state="disabled")
        self.compress_btn.pack(pady=10)

        # Progress bar
        self.progress = ttk.Progressbar(root, orient="horizontal", length=500, mode="determinate")
        self.progress.pack(pady=10)

        self.status_label = ttk.Label(root, text="", font=("Segoe UI", 11, "bold"))
        self.status_label.pack(pady=5)

        # Language switch button
        self.lang_btn = ttk.Button(root, text="🌐 Switch to RU", command=self.toggle_language)
        self.lang_btn.pack(pady=5)

        self.file_path = ""

    def toggle_language(self):
        self.current_lang = "ru" if self.current_lang == "en" else "en"
        lang = self.languages[self.current_lang]

        # Update UI text
        self.label.config(text=lang["choose_file"])
        self.choose_btn.config(text=lang["btn_choose"])
        self.preset_label.config(text=lang["preset"])
        self.compress_btn.config(text=lang["btn_compress"])
        self.lang_btn.config(text="🌐 Switch to EN" if self.current_lang == "ru" else "🌐 Switch to RU")

    def choose_file(self):
        filetypes = [("Video files", "*.mp4 *.mkv *.avi *.mov")] if self.current_lang == "en" else [("Видео файлы", "*.mp4 *.mkv *.avi *.mov")]
        self.file_path = filedialog.askopenfilename(filetypes=filetypes)
        if self.file_path:
            self.label.config(text=f"{os.path.basename(self.file_path)}")
            self.compress_btn.config(state="normal")

    def start_compression(self):
        if not self.file_path:
            return

        filetypes = [("MP4 files", "*.mp4")] if self.current_lang == "en" else [("MP4 файлы", "*.mp4")]
        output_path = filedialog.asksaveasfilename(defaultextension=".mp4", filetypes=filetypes)
        if not output_path:
            return

        preset = self.preset_var.get()
        threading.Thread(target=self.compress_video, args=(self.file_path, output_path, preset), daemon=True).start()

    def compress_video(self, input_file, output_file, preset):
        lang = self.languages[self.current_lang]
        self.compress_btn.config(state="disabled")
        self.status_label.config(text=lang["compressing"])
        self.progress["value"] = 0

        cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration",
               "-of", "default=noprint_wrappers=1:nokey=1", input_file]
        result = subprocess.run(cmd, capture_output=True, text=True)
        try:
            duration = float(result.stdout.strip())
        except:
            duration = 0

        command = [
            "ffmpeg", "-i", input_file, "-vcodec", "libx264", "-crf", "28",
            "-preset", preset, "-acodec", "aac", "-b:a", "128k", output_file, "-y"
        ]

        process = subprocess.Popen(command, stderr=subprocess.PIPE, universal_newlines=True)

        start_time = time.time()
        for line in process.stderr:
            if "time=" in line:
                timestamp = line.split("time=")[-1].split(" ")[0]
                h, m, s = 0, 0, 0
                if ":" in timestamp:
                    parts = timestamp.split(":")
                    if len(parts) == 3:
                        h, m, s = map(float, parts)
                seconds = h * 3600 + m * 60 + s
                progress_value = (seconds / duration) * 100 if duration > 0 else 0
                self.progress["value"] = progress_value

                elapsed = time.time() - start_time
                remaining = int((elapsed / (progress_value + 0.01)) * (100 - progress_value))
                self.status_label.config(text=f"{int(progress_value)}% | ~{remaining} sec left" if self.current_lang == "en" else f"{int(progress_value)}% | Осталось ~{remaining} сек")

                self.root.update_idletasks()

        process.wait()
        self.progress["value"] = 100
        self.status_label.config(text=lang["status_done"])
        self.compress_btn.config(state="normal")
        messagebox.showinfo(lang["status_done"], lang["msg_done"])

# запуск GUI
if __name__ == "__main__":
    root = tk.Tk()
    app = VideoCompressorApp(root)
    root.mainloop()
