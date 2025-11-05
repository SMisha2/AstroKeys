# AstraKeys v1.0.5 - Premium Solar Gold UI
# Integrated GUI, modes: 1-Rovny, 2-Live, 3-Hybrid, 4-Error
# by black

import time
import threading
import sys
import win32gui
import win32con
from pynput.keyboard import Controller, Key, Listener
import re
import random
import os
import winsound

from PyQt6 import QtWidgets, QtCore, QtGui

# ---------------- SONGS ----------------
SONG1 = r"""
[eT] [eT] [6eT] [ey] [6eT] [4qe] [qe] [6qe] [qE] 4 [6qe]
[eT] [eT] [6eT] [ey] [6eT] [4qe] [qe] [6qe] [qE] 4 [6qe]
6 0 [6u] [0u] 6 0 [6p] 0 [4p] 8 [4o] [8o] 4 8 [4i] 8
[eT]
"""

SONG2 = r"""
l--l--
l--l-lzlk
lshslzlklshslzlk
"""

SONG3 = r"""
fffff[4qf]spsfspsg
"""

# Key order for optional neighbor error
ROBLOX_KEYS = "1234567890qwertyuiopasdfghjklzxcvbnm"

class RobloxPianoBot:
    def __init__(self, playlist, bpm=100):
        self.keyboard = Controller()
        self.roblox_window = None
        self.lock = threading.Lock()
        self.playlist = [self.sanitize_song(song) for song in playlist if self.sanitize_song(song)]
        if not self.playlist:
            print("⚠️ Плейлист пуст после фильтрации!")
            sys.exit()
        self.song_index = 0
        self.song = self.playlist[self.song_index]
        self.bpm = bpm
        self.playing = False
        self.restart = False
        self.skip_notes = 0
        self.note_index = 0
        self.hold_star = False
        self.freeze_note = False
        self.frozen_note_index = 0
        # modes: 1-Rovny,2-Live,3-Hybrid,4-Error
        self.mode = 1
        self.start_delay = 0.03
        self.active_keys = set()
        print("🎹 AstraKeys Bot запущен!")
        print("▶ F1 - Пуск/Пауза | 🔁 F2 - Рестарт | ⏩ F3 - Пропуск 25 нот | ❌ F4 - Выход")
        print("⭐ * - Удержание нот | ❄️ F6 - Заморозка | 🎹 F7 - Следующий режим | 🎚 F5 - Предыдущий режим | 🎵 F8 - Следующая песня")
        threading.Thread(target=self.listen_keys, daemon=True).start()

    def sanitize_song(self, song):
        return re.sub(r"[^a-zA-Z0-9\[\]\s]","", song)

    def find_roblox_window(self):
        def callback(hwnd, extra):
            try:
                if "Roblox" in win32gui.GetWindowText(hwnd):
                    self.roblox_window = hwnd
            except Exception:
                pass
        win32gui.EnumWindows(callback, None)
        return self.roblox_window

    def activate_roblox(self):
        if self.find_roblox_window():
            win32gui.ShowWindow(self.roblox_window, win32con.SW_RESTORE)
            try:
                win32gui.SetForegroundWindow(self.roblox_window)
            except:
                pass
            return True
        return False

    def press_key(self, key):
        with self.lock:
            if key not in self.active_keys:
                try:
                    self.keyboard.press(key)
                except Exception:
                    pass
                self.active_keys.add(key)

    def release_key(self, key):
        with self.lock:
            if key in self.active_keys:
                try:
                    self.keyboard.release(key)
                except Exception:
                    pass
                self.active_keys.discard(key)

    def release_all(self):
        with self.lock:
            for k in list(self.active_keys):
                try:
                    self.keyboard.release(k)
                except:
                    pass
            self.active_keys.clear()

    def apply_error(self, k):
        # 5% chance to apply neighboring-key error, except edges
        try:
            if k.lower() in ["1","m"]:
                return k
            if random.random() < 0.05:
                c = k.lower()
                if c in ROBLOX_KEYS and len(c) == 1:
                    i = ROBLOX_KEYS.index(c)
                    if i == 0:
                        return ROBLOX_KEYS[1]
                    if i == len(ROBLOX_KEYS)-1:
                        return ROBLOX_KEYS[-2]
                    return ROBLOX_KEYS[i + random.choice([-1,1])]
        except Exception:
            pass
        return k

    def listen_keys(self):
        def on_press(key):
            try:
                # mode switching
                if key == Key.f7:
                    old = self.mode
                    self.mode = self.mode + 1 if self.mode < 4 else 1
                    print(f"Mode: {self.mode} (was {old})")
                    return
                if key == Key.f5:
                    old = self.mode
                    self.mode = self.mode - 1 if self.mode > 1 else 4
                    print(f"Mode: {self.mode} (was {old})")
                    return

                if key == Key.f1:
                    self.playing = not self.playing
                    print("Play" if self.playing else "Pause")
                elif key == Key.f2:
                    self.restart = True
                    print("Restart")
                elif key == Key.f3:
                    self.skip_notes += 25
                    print("Skip 25")
                elif key == Key.f4:
                    print("Exit")
                    self.release_all()
                    sys.exit()
                elif hasattr(key, "char") and key.char == "*":
                    self.hold_star = True
                    print("Pedal down")
                elif hasattr(key, "char") and key.char == "-":
                    self.start_delay = max(0.0, self.start_delay - 0.01)
                    print(f"Delay {self.start_delay}")
                elif hasattr(key, "char") and key.char == "=":
                    self.start_delay = min(0.2, self.start_delay + 0.01)
                    print(f"Delay {self.start_delay}")
                elif key == Key.f6:
                    self.freeze_note = not self.freeze_note
                    if self.freeze_note:
                        self.frozen_note_index = self.note_index
                        print(f"Freeze at {self.frozen_note_index}")
                    else:
                        print("Freeze off")
                        self.release_all()
                elif key == Key.f8:
                    self.next_song()
            except Exception as e:
                print("Key error:", e)

        def on_release(key):
            try:
                if hasattr(key, "char") and key.char == "*":
                    self.hold_star = False
                    print("Pedal up")
            except:
                pass

        with Listener(on_press=on_press, on_release=on_release) as listener:
            listener.join()

    def next_song(self):
        old_index = self.song_index
        n = len(self.playlist)
        for _ in range(n):
            self.song_index = (self.song_index + 1) % n
            if self.playlist[self.song_index]:
                self.song = self.playlist[self.song_index]
                self.note_index = 0
                self.frozen_note_index = 0
                print(f"Next song: {self.song_index+1}/{n}")
                return
        self.song_index = old_index

    def play_chord(self, chord):
        # handle mode-specific press ordering and errors
        if self.mode == 4:
            # apply potential errors to each key
            chord = [self.apply_error(k) for k in chord]

        if self.mode == 1:
            for k in chord:
                self.press_key(k)
        elif self.mode == 2:
            press_threads = []
            for k in chord:
                delay = random.uniform(0.05, 0.1)
                t = threading.Timer(delay, self.press_key, args=[k])
                t.daemon = True
                t.start()
                press_threads.append(t)
            for t in press_threads:
                t.join()
        elif self.mode == 3:
            press_delay = random.uniform(0.01, 0.03)
            for k in chord:
                t = threading.Timer(press_delay, self.press_key, args=[k])
                t.daemon = True
                t.start()

    def release_chord(self, chord):
        if self.mode == 1:
            for k in chord:
                self.release_key(k)
        elif self.mode == 2:
            for k in chord:
                delay = random.uniform(0.05, 0.2)
                t = threading.Timer(delay, self.release_key, args=[k])
                t.daemon = True
                t.start()
        elif self.mode == 3:
            for k in chord:
                delay = random.uniform(0.02, 0.08)
                t = threading.Timer(delay, self.release_key, args=[k])
                t.daemon = True
                t.start()
        else:
            # default fast release for error mode
            for k in chord:
                self.release_key(k)

    def play_song(self):
        self.activate_roblox()
        time.sleep(0.5)
        while True:
            try:
                if self.restart:
                    self.note_index = 0
                    self.frozen_note_index = 0
                    self.restart = False
                    self.release_all()
                    print("Restarted")
                    while self.hold_star and self.playing:
                        time.sleep(0.01)
                    time.sleep(0.01)
                    continue
                if not self.playing:
                    time.sleep(0.05)
                    continue
                current_index = self.frozen_note_index if self.freeze_note else self.note_index
                if current_index >= len(self.song):
                    time.sleep(0.05)
                    continue
                char = self.song[current_index]
                if self.skip_notes > 0 and not self.freeze_note:
                    if char == "[":
                        end = self.song.find("]", current_index)
                        if end != -1:
                            self.note_index = end + 1
                        else:
                            self.note_index += 1
                    else:
                        self.note_index += 1
                    self.skip_notes -= 1
                    continue
                if char.isspace():
                    if not self.freeze_note:
                        self.note_index += 1
                    continue
                while not self.hold_star and self.playing and not self.restart:
                    time.sleep(0.01)
                if char == "[":
                    end = self.song.find("]", current_index)
                    if end == -1:
                        if not self.freeze_note:
                            self.note_index += 1
                        continue
                    chord = list(self.song[current_index+1:end])
                else:
                    chord = [char]
                if self.freeze_note:
                    if self.start_delay > 0:
                        time.sleep(self.start_delay)
                    self.play_chord(chord)
                    while self.hold_star and self.playing and not self.restart:
                        time.sleep(0.05)
                    self.release_chord(chord)
                    continue
                if self.start_delay > 0:
                    time.sleep(self.start_delay)
                self.play_chord(chord)
                while self.hold_star and self.playing and not self.restart:
                    time.sleep(0.01)
                self.release_chord(chord)
                if not self.freeze_note:
                    if char == "[":
                        self.note_index = end + 1
                    else:
                        self.note_index += 1
                time.sleep(0.001)
            except Exception as e:
                print("Main loop error:", e)
                time.sleep(0.1)

# ------------------- GUI -------------------
class BotGUI(QtWidgets.QWidget):
    def __init__(self, bot: RobloxPianoBot):
        super().__init__()
        self.bot = bot
        self.setWindowTitle("AstraKeys — by black")
        # set window icon if available
        ico_path = os.path.join(os.path.dirname(__file__), 'AstraKeys.ico') if '__file__' in globals() else 'AstraKeys.ico'
        if os.path.exists(ico_path):
            try:
                self.setWindowIcon(QtGui.QIcon(ico_path))
            except:
                pass

        self.init_ui()
        self.updater = QtCore.QTimer()
        self.updater.timeout.connect(self.refresh_status)
        self.updater.start(150)
        # play startup ping
        try:
            winsound.Beep(1200,120)
        except:
            pass

    def init_ui(self):
        self.setGeometry(200,200,700,480)
        # Solar Gold palette
        dark = '#0b0b0b'
        panel = '#121212'
        gold = '#d4af37'
        soft_gold = '#ffd86a'
        text = '#f5f3f1'

        self.setStyleSheet(f"""
            QWidget{{background: {dark}; color: {text}; font-family: 'Montserrat', Arial, sans-serif;}}
            QListWidget{{background:{panel}; border:1px solid rgba(212,175,55,0.12);}}
            QTextEdit{{background:{panel}; border:1px solid rgba(212,175,55,0.08);}}
            QPushButton{{background: transparent; border:1px solid rgba(212,175,55,0.12); padding:8px; border-radius:8px;}}
            QPushButton:hover{{background: rgba(212,175,55,0.06); box-shadow: 0 0 12px rgba(212,175,55,0.12);}}
            QSlider::groove:horizontal{{height:6px; background: rgba(255,255,255,0.06); border-radius:3px;}}
            QSlider::handle:horizontal{{background:{soft_gold}; width:12px; border-radius:6px;}}
            QComboBox{{background:{panel}; border:1px solid rgba(255,216,106,0.06); padding:4px;}}
            QLabel.title{{font-size:18px; font-weight:600; color:{soft_gold};}}
            QLabel.small{{color: #9b9b9b;}}
        """)

        main = QtWidgets.QVBoxLayout()
        header = QtWidgets.QHBoxLayout()
        title = QtWidgets.QLabel("AstraKeys")
        title.setProperty('class','title')
        title.setFont(QtGui.QFont('Montserrat', 20))
        header.addWidget(title)
        header.addStretch()
        by_label = QtWidgets.QLabel("by black")
        by_label.setFont(QtGui.QFont('Montserrat', 10))
        by_label.setStyleSheet(f"color: {gold};")
        header.addWidget(by_label)
        main.addLayout(header)

        # song input
        self.song_input = QtWidgets.QTextEdit()
        self.song_input.setPlaceholderText("Вставьте текст песни здесь и нажмите 'Добавить'")
        self.song_input.setFixedHeight(100)
        main.addWidget(self.song_input)
        add_row = QtWidgets.QHBoxLayout()
        self.add_btn = QtWidgets.QPushButton("Добавить песню в список")
        add_row.addWidget(self.add_btn)
        add_row.addStretch()
        main.addLayout(add_row)
        self.add_btn.clicked.connect(self.add_song_from_input)

        # controls row
        row = QtWidgets.QHBoxLayout()
        self.start_btn = QtWidgets.QPushButton("Start / Pause (F1)")
        self.next_btn = QtWidgets.QPushButton("Next Song (F8)")
        self.prev_mode_btn = QtWidgets.QPushButton("Prev Mode (F5)")
        self.next_mode_btn = QtWidgets.QPushButton("Next Mode (F7)")
        row.addWidget(self.start_btn)
        row.addWidget(self.next_btn)
        row.addWidget(self.prev_mode_btn)
        row.addWidget(self.next_mode_btn)
        main.addLayout(row)

        # song list and status
        mid = QtWidgets.QHBoxLayout()
        self.song_list = QtWidgets.QListWidget()
        for i,s in enumerate(self.bot.playlist):
            self.song_list.addItem(f"Song {i+1} — {len(s)} chars")
        self.song_list.setCurrentRow(self.bot.song_index)
        mid.addWidget(self.song_list,2)

        right = QtWidgets.QVBoxLayout()
        self.status_label = QtWidgets.QLabel("Status: Idle")
        self.mode_label = QtWidgets.QLabel("Mode: 1")
        self.pos_label = QtWidgets.QLabel("Pos: 0")
        right.addWidget(self.status_label)
        right.addWidget(self.mode_label)
        right.addWidget(self.pos_label)
        mid.addLayout(right,1)

        main.addLayout(mid)

        # delay slider
        bottom = QtWidgets.QHBoxLayout()
        self.delay_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.delay_slider.setMinimum(0)
        self.delay_slider.setMaximum(200)
        self.delay_slider.setValue(int(self.bot.start_delay * 1000))
        self.delay_label = QtWidgets.QLabel(f"Start Delay: {self.bot.start_delay:.3f}s")
        bottom.addWidget(self.delay_label)
        bottom.addWidget(self.delay_slider)
        main.addLayout(bottom)

        # mode combo
        mode_row = QtWidgets.QHBoxLayout()
        self.mode_combo = QtWidgets.QComboBox()
        self.mode_combo.addItems(["1 - Ровный", "2 - Живой", "3 - Гибридный", "4 - Ошибочный (5%)"])
        self.mode_combo.setCurrentIndex(self.bot.mode - 1)
        mode_row.addWidget(QtWidgets.QLabel("Mode:"))
        mode_row.addWidget(self.mode_combo)
        main.addLayout(mode_row)

        help_label = QtWidgets.QLabel("F1 Start/Pause, F2 Restart, F3 Skip25, F4 Exit, F5 PrevMode, F7 NextMode, F8 NextSong")
        help_label.setProperty('class','small')
        main.addWidget(help_label)

        # footer
        footer = QtWidgets.QHBoxLayout()
        self.signature = QtWidgets.QLabel("AstraKeys — Premium · by black")
        self.signature.setFont(QtGui.QFont('Montserrat', 9))
        self.signature.setStyleSheet(f"color: {gold};")
        footer.addWidget(self.signature)
        footer.addStretch()
        main.addLayout(footer)

        # connect signals
        self.start_btn.clicked.connect(self.toggle_start)
        self.next_btn.clicked.connect(self.next_song)
        self.prev_mode_btn.clicked.connect(self.prev_mode)
        self.next_mode_btn.clicked.connect(self.next_mode)
        self.song_list.itemDoubleClicked.connect(self.select_song)
        self.delay_slider.valueChanged.connect(self.delay_changed)
        self.mode_combo.currentIndexChanged.connect(self.mode_combo_changed)

        self.setLayout(main)

    def add_song_from_input(self):
        text = self.song_input.toPlainText().strip()
        if text:
            sanitized = self.bot.sanitize_song(text)
            self.bot.playlist.append(sanitized)
            self.song_list.addItem(f"Song {len(self.bot.playlist)} — {len(sanitized)} chars")
            print("Song added")
            self.song_input.clear()

    def toggle_start(self):
        self.bot.playing = not self.bot.playing
        self.refresh_status()

    def next_song(self):
        self.bot.next_song()
        self.song_list.setCurrentRow(self.bot.song_index)
        self.refresh_status()

    def prev_mode(self):
        self.bot.mode = self.bot.mode - 1 if self.bot.mode > 1 else 4
        self.mode_combo.setCurrentIndex(self.bot.mode - 1)
        self.refresh_status()

    def next_mode(self):
        self.bot.mode = self.bot.mode + 1 if self.bot.mode < 4 else 1
        self.mode_combo.setCurrentIndex(self.bot.mode - 1)
        self.refresh_status()

    def select_song(self, item):
        row = self.song_list.currentRow()
        if 0 <= row < len(self.bot.playlist):
            self.bot.song_index = row
            self.bot.song = self.bot.playlist[row]
            self.bot.note_index = 0
            self.bot.frozen_note_index = 0
            print(f"GUI: selected {row+1}")

    def delay_changed(self, val):
        self.bot.start_delay = val / 1000.0
        self.delay_label.setText(f"Start Delay: {self.bot.start_delay:.3f}s")

    def mode_combo_changed(self, idx):
        self.bot.mode = idx + 1
        self.refresh_status()

    def refresh_status(self):
        st = "Playing" if self.bot.playing else "Paused"
        self.status_label.setText(f"Status: {st}")
        mode_names = {1: "Ровный", 2: "Живой", 3: "Гибридный", 4: "Ошибочный"}
        self.mode_label.setText(f"Mode: {self.bot.mode} — {mode_names.get(self.bot.mode,'?')}")
        self.pos_label.setText(f"Pos: {self.bot.note_index}/{len(self.bot.song)}")
        if self.mode_combo.currentIndex() != self.bot.mode - 1:
            self.mode_combo.setCurrentIndex(self.bot.mode - 1)
        if self.song_list.currentRow() != self.bot.song_index:
            self.song_list.setCurrentRow(self.bot.song_index)

# ------------------- Main runner -------------------
if __name__ == "__main__":
    playlist = [SONG1, SONG2, SONG3]
    bot = RobloxPianoBot(playlist)
    player_thread = threading.Thread(target=bot.play_song, daemon=True)
    player_thread.start()

    app = QtWidgets.QApplication(sys.argv)

    # Try to set Montserrat if installed; fallback to default
    try:
        font_db = QtGui.QFontDatabase()
        if 'Montserrat' not in font_db.families():
            # attempt to load from local file if present
            local_ttf = os.path.join(os.path.dirname(__file__) if '__file__' in globals() else '.', 'Montserrat-Regular.ttf')
            if os.path.exists(local_ttf):
                font_id = font_db.addApplicationFont(local_ttf)
                print('Loaded Montserrat from file', font_id)
    except Exception:
        pass

    gui = BotGUI(bot)
    gui.show()
    sys.exit(app.exec())
