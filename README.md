# SyncSplice 🎬🎵
**Random Video Slice + Audio Mashup Tool**

SyncSplice is a simple Python + Tkinter desktop app that takes any short audio file and pairs it with a random segment from a longer video (segment length = audio length + 1 second).
The result is exported as an MP4 (`H.264` video + `AAC` audio) using [FFmpeg](https://ffmpeg.org/).

It was used as a way to put narration over a random minecraft parkour clip for TikTok. Maybe You'll find a different way to use it.

---

## ✨ Features
- **Random segment selection** — picks a random slice from your long video.
- **Automatic length matching** — segment is always `audio length + 1s`.
- **Desktop GUI** — built with Tkinter for easy file selection.
- **Progress bar + live log** — see FFmpeg’s progress in real time.
- **Custom quality settings** — adjust CRF and encoding preset.
- **Reproducible randomness** — optional seed for same results every time.
- **Cross-platform** — works on Linux, Windows, macOS (Steam Deck friendly).

---

## 📦 Requirements
- Python 3.7+
- [FFmpeg](https://ffmpeg.org/) installed and available in your system PATH.

### Install FFmpeg
On **Arch Linux / SteamOS**:
```bash
