#!/usr/bin/env python3
import subprocess, json, math, os, random, re, threading, queue, time, sys
from tkinter import Tk, StringVar, IntVar, BooleanVar, ttk, filedialog, messagebox, END, DISABLED, NORMAL

def ffprobe_duration(path):
    out = subprocess.check_output([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json", path
    ], text=True)
    data = json.loads(out)
    dur = float(data["format"]["duration"])
    if not math.isfinite(dur) or dur <= 0:
        raise ValueError("Non-positive duration")
    return dur

def fmt_secs(s):
    # return HH:MM:SS.mmm
    ms = int(round((s - int(s)) * 1000))
    s = int(s)
    h = s // 3600
    m = (s % 3600) // 60
    sec = s % 60
    return f"{h:02d}:{m:02d}:{sec:02d}.{ms:03d}"

class MashupApp:
    def __init__(self, root):
        self.root = root
        root.title("SyncSplice")
        root.geometry("720x520")

        self.video_path = StringVar()
        self.audio_path = StringVar()
        self.out_path   = StringVar()
        self.crf        = IntVar(value=20)
        self.preset     = StringVar(value="veryfast")
        self.seed_str   = StringVar(value="")
        self.keep_v_audio_tail = BooleanVar(value=False)  # optional future feature

        pad = 8

        frm = ttk.Frame(root, padding=pad)
        frm.pack(fill="both", expand=True)

        # Row: Video
        row = 0
        ttk.Label(frm, text="Video:").grid(column=0, row=row, sticky="w")
        ent_video = ttk.Entry(frm, textvariable=self.video_path, width=70)
        ent_video.grid(column=1, row=row, sticky="we", padx=(6,6))
        ttk.Button(frm, text="Browse", command=self.browse_video).grid(column=2, row=row, sticky="e")
        row += 1

        # Row: Audio
        ttk.Label(frm, text="Audio:").grid(column=0, row=row, sticky="w")
        ent_audio = ttk.Entry(frm, textvariable=self.audio_path, width=70)
        ent_audio.grid(column=1, row=row, sticky="we", padx=(6,6))
        ttk.Button(frm, text="Browse", command=self.browse_audio).grid(column=2, row=row, sticky="e")
        row += 1

        # Row: Output
        ttk.Label(frm, text="Output MP4:").grid(column=0, row=row, sticky="w")
        ent_out = ttk.Entry(frm, textvariable=self.out_path, width=70)
        ent_out.grid(column=1, row=row, sticky="we", padx=(6,6))
        ttk.Button(frm, text="Save as…", command=self.choose_out).grid(column=2, row=row, sticky="e")
        row += 1

        # Row: Options
        optfrm = ttk.Frame(frm)
        optfrm.grid(column=0, row=row, columnspan=3, sticky="we", pady=(6,0))
        ttk.Label(optfrm, text="CRF:").grid(column=0, row=0, sticky="w")
        spn_crf = ttk.Spinbox(optfrm, from_=12, to=28, textvariable=self.crf, width=5)
        spn_crf.grid(column=1, row=0, padx=(4,12), sticky="w")

        ttk.Label(optfrm, text="Preset:").grid(column=2, row=0, sticky="w")
        cmb = ttk.Combobox(optfrm, textvariable=self.preset, values=[
            "ultrafast","superfast","veryfast","faster","fast","medium","slow","slower","veryslow"
        ], width=12, state="readonly")
        cmb.grid(column=3, row=0, padx=(4,12), sticky="w")

        ttk.Label(optfrm, text="Seed (optional):").grid(column=4, row=0, sticky="w")
        ent_seed = ttk.Entry(optfrm, textvariable=self.seed_str, width=12)
        ent_seed.grid(column=5, row=0, padx=(4,0), sticky="w")

        row += 1

        # Row: Progress
        self.progress = ttk.Progressbar(frm, mode="determinate", maximum=100)
        self.progress.grid(column=0, row=row, columnspan=3, sticky="we", pady=(6,0))
        row += 1

        # Row: Log
        ttk.Label(frm, text="Log:").grid(column=0, row=row, sticky="w", pady=(6,0))
        row += 1

        self.txt = ttk.Treeview()  # we’ll actually use a Text widget for logs
        self.log = ttk.Frame(frm)
        self.log.grid(column=0, row=row, columnspan=3, sticky="nsew")
        frm.rowconfigure(row, weight=1)
        row += 1

        self.txtbox = ttk.Entry  # placeholder to satisfy linter
        from tkinter import Text
        self.txtbox = Text(self.log, height=14, wrap="word")
        self.txtbox.pack(fill="both", expand=True)
        self.txtbox.configure(state=DISABLED)

        # Row: Buttons
        btnfrm = ttk.Frame(frm)
        btnfrm.grid(column=0, row=row, columnspan=3, sticky="we", pady=(8,0))
        row += 1

        self.run_btn = ttk.Button(btnfrm, text="Make MP4", command=self.on_run)
        self.run_btn.pack(side="left")
        ttk.Button(btnfrm, text="Quit", command=root.destroy).pack(side="right")

        # queues/threads
        self.q = queue.Queue()
        self.worker = None
        self.stop_flag = False

        # column weights
        frm.columnconfigure(1, weight=1)

        # periodic UI updater
        self.root.after(100, self.pump_queue)

    def browse_video(self):
        path = filedialog.askopenfilename(title="Choose video", filetypes=[("Video files","*.mp4 *.mkv *.mov *.webm *.avi"), ("All files","*.*")])
        if path:
            self.video_path.set(path)
            if not self.out_path.get():
                base, _ = os.path.splitext(os.path.basename(path))
                self.out_path.set(os.path.join(os.path.dirname(path), f"{base}_mashup.mp4"))

    def browse_audio(self):
        path = filedialog.askopenfilename(title="Choose audio", filetypes=[("Audio","*.mp3 *.wav *.m4a *.aac *.flac *.ogg"), ("All files","*.*")])
        if path:
            self.audio_path.set(path)

    def choose_out(self):
        path = filedialog.asksaveasfilename(defaultextension=".mp4", filetypes=[("MP4 video","*.mp4")], title="Save output as…")
        if path:
            self.out_path.set(path)

    def log_line(self, s):
        self.txtbox.configure(state=NORMAL)
        self.txtbox.insert(END, s + "\n")
        self.txtbox.see(END)
        self.txtbox.configure(state=DISABLED)

    def set_progress(self, pct):
        pct = max(0, min(100, pct))
        self.progress['value'] = pct

    def pump_queue(self):
        try:
            while True:
                kind, payload = self.q.get_nowait()
                if kind == "log":
                    self.log_line(payload)
                elif kind == "progress":
                    self.set_progress(payload)
                elif kind == "done":
                    self.run_btn.config(state=NORMAL)
                    if payload == 0:
                        messagebox.showinfo("Done", "Export finished.")
                    else:
                        messagebox.showerror("Error", f"ffmpeg failed (code {payload}). See log.")
                elif kind == "status":
                    self.run_btn.config(text=payload)
        except queue.Empty:
            pass
        self.root.after(100, self.pump_queue)

    def on_run(self):
        video = self.video_path.get().strip()
        audio = self.audio_path.get().strip()
        outp  = self.out_path.get().strip()

        if not video or not os.path.exists(video):
            messagebox.showwarning("Missing video", "Please choose a valid input video.")
            return
        if not audio or not os.path.exists(audio):
            messagebox.showwarning("Missing audio", "Please choose a valid input audio.")
            return
        if not outp:
            messagebox.showwarning("Missing output", "Please choose an output path.")
            return

        try:
            vdur = ffprobe_duration(video)
            adur = ffprobe_duration(audio)
        except Exception as e:
            messagebox.showerror("ffprobe error", str(e))
            return

        seg_len = adur + 1.0
        if seg_len > vdur:
            messagebox.showerror("Video too short",
                                 f"Need at least {seg_len:.3f}s of video, but video is {vdur:.3f}s.")
            return

        seed_val = None
        if self.seed_str.get().strip():
            try:
                seed_val = int(self.seed_str.get().strip())
            except ValueError:
                messagebox.showwarning("Seed ignored", "Seed must be an integer. Continuing without it.")

        rng = random.Random(seed_val)
        max_start = max(0.0, vdur - seg_len)
        start = rng.uniform(0.0, max_start)

        crf = int(self.crf.get())
        preset = self.preset.get()

        # Launch worker thread
        self.run_btn.config(state=DISABLED, text="Working…")
        self.set_progress(0)
        self.txtbox.configure(state=NORMAL)
        self.txtbox.delete("1.0", END)
        self.txtbox.configure(state=DISABLED)

        self.worker = threading.Thread(
            target=self.encode_worker,
            args=(video, audio, outp, start, seg_len, crf, preset, adur),
            daemon=True
        )
        self.worker.start()

    def encode_worker(self, video, audio, outp, start, seg_len, crf, preset, adur):
        try:
            self.q.put(("log", f"[info] Video segment: start={start:.3f}s length={seg_len:.3f}s (audio {adur:.3f}s + 1s)"))
            self.q.put(("log", f"[info] Output: {outp}"))
            # ffmpeg command:
            #   - cut video slice
            #   - pad provided audio with silence to exactly seg_len
            #   - encode H.264/AAC mp4 with faststart
            cmd = [
                "ffmpeg", "-y",
                "-ss", f"{start:.3f}", "-t", f"{seg_len:.3f}", "-i", video,
                "-i", audio,
                "-filter_complex", "[1:a]apad[aud]",
                "-map", "0:v:0", "-map", "[aud]",
                "-c:v", "libx264", "-preset", preset, "-crf", str(crf),
                "-c:a", "aac", "-b:a", "192k",
                "-movflags", "+faststart",
                "-shortest",  # ensures output stops at the shorter of v/a if something goes odd
                outp
            ]

            # Run and parse progress from stderr time=
            proc = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.DEVNULL, text=True, bufsize=1, universal_newlines=True)
            time_re = re.compile(r"time=(\d+):(\d+):(\d+)\.(\d+)")
            target = seg_len if seg_len > 0 else 1.0

            for line in proc.stderr:
                line = line.rstrip()
                if line:
                    self.q.put(("log", line))
                m = time_re.search(line)
                if m:
                    hh, mm, ss, ms = m.groups()
                    cur = (int(hh)*3600 + int(mm)*60 + int(ss)) + int(ms)/100.0
                    pct = (cur / target) * 100.0
                    self.q.put(("progress", pct if pct <= 100 else 100))
            ret = proc.wait()
            self.q.put(("progress", 100 if ret == 0 else self.progress['value']))
            self.q.put(("done", ret))
            self.q.put(("status", "Make MP4"))
        except Exception as e:
            self.q.put(("log", f"[error] {e}"))
            self.q.put(("done", 1))
            self.q.put(("status", "Make MP4"))

def main():
    root = Tk()
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except:
        pass
    app = MashupApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
