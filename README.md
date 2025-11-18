# 📱 Sudoku App

A simple and lightweight Sudoku game built with **Python**, **Kivy**, and **Buildozer**, packaged for Android. The project includes a Sudoku puzzle generator, a clean UI, and persistent score tracking.

## ✨ Features

* Generate valid Sudoku boards on demand
* Interactive 9x9 grid
* Error checking & validation
* Animated UI elements
* Touch-friendly interface for mobile
* Local records stored in `records.json`
* Android APK included (`bin/sudoku-0.1-arm64-v8a_armeabi-v7a-debug.apk`)

## 🧩 Project Structure

```
SudokuApp/
│
├── main.py               # Main Kivy application
├── sudoku_generator.py   # Puzzle generator logic
├── sudoku_puzzle.py      # Board operations and validation
├── sudoku_widgets.py     # Custom UI widgets
├── data/                 # Icons, frames, splash images
├── records.json          # Saved scores and history
└── buildozer.spec        # Buildozer configuration for Android
```

## 📦 How to Run (Desktop)

```bash
pip install kivy
python main.py
```

## 📱 Build Android APK

```bash
pip install buildozer
buildozer -v android debug
```

## 📄 License

MIT License.


