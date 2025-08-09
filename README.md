# SyncSplice 🎬🎵
**Random Video Slice + Audio Mashup Tool**

SyncSplice is a simple Python + Tkinter desktop app that takes any short audio file and pairs it with a random segment from a longer video (segment length = audio length + 1 second).  
The result is exported as an MP4 (`H.264` video + `AAC` audio) using [FFmpeg](https://ffmpeg.org/).

Perfect for quick meme edits, random mashups, or matching your favorite music to random video moments.

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
sudo pacman -S --needed ffmpeg
```

On **Debian/Ubuntu**:
```bash
sudo apt install ffmpeg
```

On **macOS** (Homebrew):
```bash
brew install ffmpeg
```

---

## 🚀 Installation
Clone this repository and install requirements (Tkinter is included with most Python installations):

```bash
git clone https://github.com/Lerion99/syncsplice.git
cd syncsplice
chmod +x mashup_gui.py
```

---

## 🖥 Usage
Run the app:
```bash
python3 mashup_gui.py
```

1. **Select a video file** (long source video).
2. **Select an audio file** (short clip you want to overlay).
3. **Choose output MP4 path**.
4. Optionally set:
   - **CRF** (quality, lower = better)
   - **Preset** (encoding speed/efficiency)
   - **Random seed** (to repeat the same selection)
5. Click **Make MP4** and wait for FFmpeg to finish.

---

## 🎯 Example
- Video: `minecraft_parkour.mp4` (1 hour long)  
- Audio: `song.mp3` (2 min long)  

SyncSplice will:
- Pick a random segment 2m 1s long from the video.
- Place your audio over it (silence fills last 1s).
- Save it as `output.mp4`.

---

## 📜 License
This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## 💡 Ideas for future features
- Mix last second with original video audio instead of silence.
- Batch mode for generating multiple random clips.
- Drag & drop file support.
- Export as GIF or WebM.

---
