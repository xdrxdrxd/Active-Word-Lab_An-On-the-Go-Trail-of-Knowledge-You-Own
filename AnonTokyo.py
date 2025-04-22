# -*- coding: utf-8 -*-
import os
import sqlite3
import datetime
import csv
import logging
import re
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.config import Config
from kivy.core.audio import SoundLoader
from kivy.metrics import dp
from kivy.utils import platform
from gtts import gTTS
import google.generativeai as genai
from google.api_core import exceptions

# Android-specific imports
if platform == 'android':
    from android.storage import app_storage_path

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Set working directory
if platform == 'android':
    BASE_DIR = app_storage_path()
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)
logging.info(f"Working directory set to: {BASE_DIR}")

# Font setup
font_path = os.path.join(BASE_DIR, "NotoSansSC-Regular.ttf")
if not os.path.exists(font_path):
    raise FileNotFoundError(f"Font file not found: {font_path}. Please download NotoSansSC-Regular.ttf.")
LabelBase.register(name="CustomFont", fn_regular=font_path)

# Kivy configuration for Android
Config.set('graphics', 'resizable', 0)
Config.set('graphics', 'multisamples', 0)
Config.set('graphics', 'maxfps', 60)
Config.set('input', 'mouse', 'mouse,disable_multitouch')

# File paths
DB_PATH = os.path.join(BASE_DIR, 'vocabulary.db')
EXPORT_PATH = os.path.join(BASE_DIR, 'vocabulary_export.csv')
WORDS_DATASET_PATH = os.path.join(BASE_DIR, 'unigram_freq.csv')
TOP_WORDS_FILE = os.path.join(BASE_DIR, 'top_words.txt')

# ─── Database Manager ─────────────────────────────────────────────────────────
class DatabaseManager:
    _conn = None

    @classmethod
    def get_connection(cls):
        if cls._conn is None:
            cls._conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        return cls._conn

    @classmethod
    def close_connection(cls):
        if cls._conn:
            cls._conn.close()
            cls._conn = None

# ─── Database Functions ─────────────────────────────────────────────────────────
def init_settings_table():
    """Initialize the settings table for storing the API key and model."""
    conn = DatabaseManager.get_connection()
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )''')
    conn.commit()
    logging.info("Settings table initialized")

def get_api_key():
    """Retrieve the API key from the database."""
    conn = DatabaseManager.get_connection()
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key = 'api_key'")
    result = c.fetchone()
    return result[0] if result else None

def get_api_model():
    """Retrieve the API model from the database, default to 'gemini-1.5-flash'."""
    conn = DatabaseManager.get_connection()
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key = 'api_model'")
    result = c.fetchone()
    return result[0] if result else 'gemini-1.5-flash'

def save_api_key(api_key):
    """Save or update the API key in the database."""
    conn = DatabaseManager.get_connection()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('api_key', ?)", (api_key,))
    conn.commit()
    logging.info("API key saved to database")

def save_api_model(api_model):
    """Save or update the API model in the database."""
    conn = DatabaseManager.get_connection()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('api_model', ?)", (api_model or 'gemini-1.5-flash',))
    conn.commit()
    logging.info(f"API model saved to database: {api_model or 'gemini-1.5-flash'}")

def clear_api_key():
    """Clear the API key from the database."""
    conn = DatabaseManager.get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM settings WHERE key = 'api_key'")
    conn.commit()
    logging.info("API key cleared from database")

def clear_api_model():
    """Clear the API model from the database (reset to default)."""
    conn = DatabaseManager.get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM settings WHERE key = 'api_model'")
    conn.commit()
    logging.info("API model cleared from database")

def configure_genai():
    """Configure the Gemini API with the stored API key and model, and validate it."""
    api_key = get_api_key()
    api_model = get_api_model()
    if not api_key:
        logging.error("No API key found. Please set it in the Settings screen.")
        return False
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(api_model)
        model.generate_content("Test")
        logging.info(f"Gemini API configured and validated successfully with model: {api_model}")
        return True
    except exceptions.InvalidArgument as e:
        logging.error(f"Invalid API key or model: {e}")
        return False
    except Exception as e:
        logging.error(f"Failed to configure Gemini API with model {api_model}: {e}")
        return False

# ─── Word List Generation ─────────────────────────────────────────────────────────
def generate_top_words(limit=10000):
    """Generate a list of high-frequency words from unigram_freq.csv."""
    if os.path.exists(TOP_WORDS_FILE):
        logging.info(f"Top words list already exists: {TOP_WORDS_FILE}")
        return
    if not os.path.exists(WORDS_DATASET_PATH):
        raise FileNotFoundError(f"Dataset file not found: {WORDS_DATASET_PATH}. Please download unigram_freq.csv from Kaggle.")
    
    word_freq = []
    try:
        with open(WORDS_DATASET_PATH, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)
            for row in reader:
                if len(row) < 2:
                    continue
                word = row[0].strip().lower()
                freq = int(row[1])
                if is_valid_word(word):
                    word_freq.append((word, freq))
        word_freq.sort(key=lambda x: x[1], reverse=True)
        top_words = [wf[0] for wf in word_freq[:limit]]
        with open(TOP_WORDS_FILE, 'w', encoding='utf-8') as tf:
            for word in top_words:
                tf.write(word + '\n')
        logging.info(f"Generated top {len(top_words)} words list to {TOP_WORDS_FILE}")
    except Exception as e:
        logging.error(f"Failed to generate top words list: {e}")
        raise

def get_next_words(n=10):
    """Get words from top_words.txt that are not in the database."""
    conn = DatabaseManager.get_connection()
    cur = conn.cursor()
    try:
        if not os.path.exists(TOP_WORDS_FILE):
            generate_top_words()
        with open(TOP_WORDS_FILE, 'r', encoding='utf-8') as f:
            all_top_words = [line.strip() for line in f if line.strip()]
        cur.execute("SELECT word FROM words")
        existing_words = set(row[0] for row in cur.fetchall())
        available_words = [word for word in all_top_words if word not in existing_words]
        words_to_add = available_words[:n]
        logging.info(f"Found {len(words_to_add)} words to add")
        return words_to_add
    except Exception as e:
        logging.error(f"Failed to get next words: {e}")
        return []

# ─── Database Operations ─────────────────────────────────────────────────────────
def create_database():
    """Initialize the words table."""
    conn = DatabaseManager.get_connection()
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS words (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        word TEXT UNIQUE NOT NULL,
        example TEXT,
        zh_translation TEXT,
        ja_translation TEXT,
        zh_example_translation TEXT,
        ja_example_translation TEXT,
        pos TEXT,
        tense TEXT,
        familiarity INTEGER DEFAULT 1,
        last_reviewed DATE,
        learned BOOLEAN DEFAULT 0,
        mastered BOOLEAN DEFAULT 0,
        interval INTEGER DEFAULT 1,
        next_review DATE
    )''')
    c.execute('CREATE INDEX IF NOT EXISTS idx_word ON words(word)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_learned ON words(learned)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_mastered ON words(mastered)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_next_review ON words(next_review)')
    conn.commit()
    logging.info("Words table and indexes initialized")

def reset_database():
    """Reset the words table."""
    conn = DatabaseManager.get_connection()
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS words")
    c.execute('''
    CREATE TABLE words (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        word TEXT UNIQUE NOT NULL,
        example TEXT,
        zh_translation TEXT,
        ja_translation TEXT,
        zh_example_translation TEXT,
        ja_example_translation TEXT,
        pos TEXT,
        tense TEXT,
        familiarity INTEGER DEFAULT 1,
        last_reviewed DATE,
        learned BOOLEAN DEFAULT 0,
        mastered BOOLEAN DEFAULT 0,
        interval INTEGER DEFAULT 1,
        next_review DATE
    )''')
    conn.commit()
    logging.info("Words table reset")

def check_database_stats():
    """Check database statistics."""
    conn = DatabaseManager.get_connection()
    c = conn.cursor()
    stats = {}
    try:
        c.execute("SELECT COUNT(*) FROM words")
        stats['total'] = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM words WHERE learned=0")
        stats['unlearned'] = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM words WHERE learned=1 AND mastered=0")
        stats['learned_not_mastered'] = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM words WHERE mastered=1")
        stats['mastered'] = c.fetchone()[0]
        logging.info(f"Database stats: total={stats['total']}, unlearned={stats['unlearned']}, learned_not_mastered={stats['learned_not_mastered']}, mastered={stats['mastered']}")
    except Exception as e:
        logging.error(f"Failed to check database stats: {e}")
    return stats

def is_valid_word(word):
    """Check if the word contains only letters."""
    return bool(word and re.match(r'^[a-zA-Z]+$', word))

def fetch_word_details(word):
    """Fetch word details from Gemini API."""
    example, zh_trans, ja_trans, zh_example_trans, ja_example_trans, pos, tense = '', '', '', '', '', '未知', '未知'
    try:
        model = genai.GenerativeModel(get_api_model())
        prompt = (f"Provide the following for the English word '{word}':\n"
                  f"1. Its direct Chinese translation in Traditional Chinese (no pinyin).\n"
                  f"2. Its direct Japanese translation (no romaji).\n"
                  f"3. An example sentence using the word.\n"
                  f"4. The Chinese translation of the example sentence in Traditional Chinese (no pinyin).\n"
                  f"5. The Japanese translation of the example sentence (no romaji).\n"
                  f"6. Part of speech.\n"
                  f"7. Tense changes (if applicable).\n"
                  f"Format as:\n"
                  f"Chinese Translation: <zh_trans>\n"
                  f"Japanese Translation: <ja_trans>\n"
                  f"Example: <sentence>\n"
                  f"Chinese Example Translation: <zh_example_trans>\n"
                  f"Japanese Example Translation: <ja_example_trans>\n"
                  f"Part of Speech: <pos>\n"
                  f"Tense Changes: <tense>")
        resp = model.generate_content(prompt)
        lines = [l for l in resp.text.strip().split('\n') if l]
        zh_trans = lines[0].replace('Chinese Translation: ', '') if len(lines) > 0 else ''
        ja_trans = lines[1].replace('Japanese Translation: ', '') if len(lines) > 1 else ''
        example = lines[2].replace('Example: ', '') if len(lines) > 2 else ''
        zh_example_trans = lines[3].replace('Chinese Example Translation: ', '') if len(lines) > 3 else ''
        ja_example_trans = lines[4].replace('Japanese Example Translation: ', '') if len(lines) > 4 else ''
        pos = lines[5].replace('Part of Speech: ', '') if len(lines) > 5 and lines[5].replace('Part of Speech: ', '') else '未知'
        tense = lines[6].replace('Tense Changes: ', '') if len(lines) > 6 and lines[6].replace('Tense Changes: ', '') else '未知'
        logging.info(f"Fetched details for word {word}: POS={pos}, tense={tense}, zh_trans={zh_trans}, ja_trans={ja_trans}")
    except Exception as e:
        logging.error(f"Failed to fetch details for word {word}: {e}")
    return example, zh_trans, ja_trans, zh_example_trans, ja_example_trans, pos, tense

def import_words_from_csv():
    """Import words from CSV file."""
    conn = DatabaseManager.get_connection()
    cur = conn.cursor()
    try:
        if not os.path.exists(EXPORT_PATH):
            logging.warning(f"Import file {EXPORT_PATH} does not exist")
            return 0
        with open(EXPORT_PATH, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)
            batch = []
            for row in reader:
                if len(row) < 15:
                    continue
                word = row[1].strip().lower()
                if not is_valid_word(word):
                    logging.warning(f"Invalid word: {word}, skipping")
                    continue
                cur.execute("SELECT COUNT(*) FROM words WHERE word = ?", (word,))
                if cur.fetchone()[0] > 0:
                    logging.warning(f"Word {word} already exists, skipping")
                    continue
                batch.append((word, row[2], row[3], row[4], row[5], row[6], row[7], row[8], 
                              int(row[9] or 1), row[10], int(row[11] or 0), int(row[12] or 0), 
                              int(row[13] or 1), row[14] or None))
            cur.executemany('''INSERT INTO words (word, example, zh_translation, ja_translation, 
                            zh_example_translation, ja_example_translation, pos, tense, familiarity, 
                            last_reviewed, learned, mastered, interval, next_review)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', batch)
            conn.commit()
            logging.info(f"Imported {len(batch)} words")
            return len(batch)
    except Exception as e:
        logging.error(f"Import failed: {e}")
        return 0

def get_words_for_mode(mode):
    """Get words based on mode."""
    conn = DatabaseManager.get_connection()
    cur = conn.cursor()
    rows = []
    try:
        today = datetime.date.today().isoformat()
        if mode == 'learn':
            cur.execute("SELECT * FROM words WHERE learned=0")
        elif mode == 'review':
            cur.execute("SELECT * FROM words WHERE learned=1 AND mastered=0 AND next_review <= ?", (today,))
        else:  # mastered
            cur.execute("SELECT * FROM words WHERE mastered=1")
        rows = cur.fetchall()
        logging.info(f"Loaded {len(rows)} words for mode {mode}")
        if len(rows) > 0:
            logging.info(f"Loaded words: {[row[1] for row in rows]}")
        else:
            logging.warning(f"No words found for mode {mode}")
    except Exception as e:
        logging.error(f"Failed to query words: {e}")
    return rows

def play_word(word):
    """Play word audio using cache with SoundLoader."""
    try:
        audio_dir = os.path.join(BASE_DIR, 'audio')
        if not os.path.exists(audio_dir):
            os.makedirs(audio_dir)
            logging.info(f"Created audio directory: {audio_dir}")

        filename = os.path.join(audio_dir, f'tts_{word}.mp3')
        if not os.path.exists(filename):
            tts = gTTS(text=word, lang='en')
            if not os.access(audio_dir, os.W_OK):
                logging.error(f"No write permission for directory: {audio_dir}")
                raise PermissionError(f"No write permission for directory: {audio_dir}")
            tts.save(filename)
            logging.info(f"Generated audio file: {filename}")

        # Stop any currently playing sound
        if hasattr(play_word, 'current_sound') and play_word.current_sound:
            play_word.current_sound.stop()
        
        # Load and play new sound
        sound = SoundLoader.load(filename)
        if sound:
            play_word.current_sound = sound
            sound.play()
            logging.info(f"Playing audio for word {word}")
        else:
            logging.error(f"Failed to load audio file: {filename}")
    except PermissionError as e:
        logging.error(f"Audio playback failed (permission issue): {e}")
    except Exception as e:
        logging.error(f"Audio playback failed: {e}")

def manage_audio_cache(max_size_mb=100):
    """Manage audio cache to prevent storage bloat."""
    audio_dir = os.path.join(BASE_DIR, 'audio')
    if not os.path.exists(audio_dir):
        return
    total_size = 0
    files = []
    for f in os.listdir(audio_dir):
        path = os.path.join(audio_dir, f)
        if os.path.isfile(path) and f.endswith('.mp3'):
            size = os.path.getsize(path) / (1024 * 1024)
            total_size += size
            files.append((path, os.path.getmtime(path)))
    if total_size > max_size_mb:
        files.sort(key=lambda x: x[1])
        for path, _ in files:
            if total_size <= max_size_mb:
                break
            total_size -= os.path.getsize(path) / (1024 * 1024)
            os.remove(path)
            logging.info(f"Deleted audio file: {path}")

# ─── Main Menu ─────────────────────────────────────────────────────────
class MainMenu(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        root_layout = FloatLayout(size_hint=(1, 1))
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False, do_scroll_y=True)
        layout = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=max(20, Window.width * 0.04),
            padding=[max(30, Window.width * 0.05)] * 4
        )
        layout.bind(minimum_height=layout.setter('height'))

        layout.add_widget(Label(
            text='單字訓練',
            font_size=max(40, Window.width * 0.06),
            font_name='CustomFont',
            size_hint_y=None,
            height=max(60, Window.height * 0.08)
        ))

        btns = ['學習模式', '複習模式', '已學習單字', '新增單字', '匯入單字', '匯出', '檢查資料庫', '重製資料庫', '設置 API 金鑰', '幫助']
        for b in btns:
            btn = Button(
                text=b,
                font_name='CustomFont',
                size_hint_y=None,
                height=max(60, Window.height * 0.08),
                font_size=max(20, Window.width * 0.035)
            )
            if b == '匯出':
                btn.bind(on_press=self.export)
            elif b == '匯入單字':
                btn.bind(on_press=self.import_words)
            elif b == '重製資料庫':
                btn.bind(on_press=self.reset_database)
            elif b == '檢查資料庫':
                btn.bind(on_press=self.check_database)
            elif b == '設置 API 金鑰':
                btn.bind(on_press=lambda x: self.switch_screen('設置 API 金鑰'))
            else:
                btn.bind(on_press=lambda x, screen=b: self.switch_screen(screen))
            layout.add_widget(btn)

        self.status_label = Label(
            text='',
            font_name='CustomFont',
            size_hint_y=None,
            height=max(40, Window.height * 0.05),
            font_size=max(16, Window.width * 0.025)
        )
        layout.add_widget(self.status_label)
        scroll.add_widget(layout)
        root_layout.add_widget(scroll)

        author_label = Label(
            text='X:@Biggg48763',
            font_name='CustomFont',
            font_size=14,
            color=(0.7, 0.7, 0.7, 1),
            pos_hint={'right': 0.95, 'bottom': 0.05},
            size_hint=(None, None),
            size=(150, 30)
        )
        root_layout.add_widget(author_label)
        self.add_widget(root_layout)
        Window.bind(on_resize=self.on_window_resize)

    def on_window_resize(self, window, width, height):
        self.rebuild_layout()
        logging.info(f"Window resized: {width}x{height}")

    def rebuild_layout(self):
        self.clear_widgets()
        self.__init__()

    def switch_screen(self, screen_name):
        self.manager.current = screen_name
        logging.info(f"Switched to screen: {screen_name}")

    def reset_database(self, instance):
        reset_database()
        self.status_label.text = "資料庫已重製（所有單字已清空）"
        logging.info("Database reset")

    def export(self, instance):
        try:
            conn = DatabaseManager.get_connection()
            cur = conn.cursor()
            cur.execute("SELECT * FROM words")
            rows = cur.fetchall()
            with open(EXPORT_PATH, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['id', 'word', 'example', 'zh_translation', 'ja_translation', 'zh_example_translation', 'ja_example_translation', 'pos', 'tense', 'familiarity', 'last_reviewed', 'learned', 'mastered', 'interval', 'next_review'])
                writer.writerows(rows)
            logging.info(f"Exported to {EXPORT_PATH}")
            self.status_label.text = "匯出成功"
        except Exception as e:
            logging.error(f"Export failed: {e}")
            self.status_label.text = "匯出失敗"

    def import_words(self, instance):
        self.status_label.text = '正在匯入單字...'
        Clock.schedule_once(lambda dt: self._import_words_thread(), 0)

    def _import_words_thread(self):
        count = import_words_from_csv()
        self.status_label.text = f'已匯入 {count} 個單字'

    def check_database(self, instance):
        stats = check_database_stats()
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        stats_text = (f"總單字數：{stats['total']}\n"
                      f"未學習：{stats['unlearned']}\n"
                      f"已學習未掌握：{stats['learned_not_mastered']}\n"
                      f"已掌握：{stats['mastered']}")
        stats_label = Label(
            text=stats_text,
            font_name='CustomFont',
            font_size=max(18, Window.width * 0.025),
            halign='left',
            valign='top',
            size_hint_y=None,
            height=max(120, Window.height * 0.2)
        )
        stats_label.bind(size=lambda instance, value: setattr(stats_label, 'text_size', (stats_label.width * 0.9, None)))
        close_btn = Button(
            text='關閉',
            font_name='CustomFont',
            size_hint_y=None,
            height=max(48, Window.height * 0.06),
            font_size=max(18, Window.width * 0.03)
        )
        content.add_widget(stats_label)
        content.add_widget(close_btn)
        popup = Popup(
            title='資料庫統計',
            title_font='CustomFont',
            title_size=max(20, Window.width * 0.03),
            content=content,
            size_hint=(0.8, 0.6)
        )
        close_btn.bind(on_press=popup.dismiss)
        popup.open()
        logging.info("Displayed database stats popup")

# ─── Settings Screen for API Key and Model ─────────────────────────────────────────────────────────
class SettingsScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False, do_scroll_y=True)
        layout = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=max(15, Window.width * 0.02),
            padding=[max(20, Window.width * 0.03)] * 4
        )
        layout.bind(minimum_height=layout.setter('height'))

        self.api_key_input = TextInput(
            font_name='CustomFont',
            hint_text='請輸入 Gemini API 金鑰',
            size_hint_y=None,
            height=max(60, Window.height * 0.08),
            font_size=max(18, Window.width * 0.03),
            password=True
        )
        self.api_model_input = TextInput(
            font_name='CustomFont',
            hint_text='請輸入 API 模型（留空使用 gemini-1.5-flash）',
            size_hint_y=None,
            height=max(60, Window.height * 0.08),
            font_size=max(18, Window.width * 0.03)
        )
        self.status_label = Label(
            text='',
            font_name='CustomFont',
            size_hint_y=None,
            height=max(40, Window.height * 0.05),
            font_size=max(16, Window.width * 0.025)
        )
        layout.add_widget(self.api_key_input)
        layout.add_widget(self.api_model_input)
        layout.add_widget(self.status_label)
        btn_save = Button(
            text='儲存',
            font_name='CustomFont',
            size_hint_y=None,
            height=max(48, Window.height * 0.06),
            font_size=max(18, Window.width * 0.03),
            on_press=self.save_settings
        )
        btn_clear = Button(
            text='清除 API 設定',
            font_name='CustomFont',
            size_hint_y=None,
            height=max(48, Window.height * 0.06),
            font_size=max(18, Window.width * 0.03),
            on_press=self.clear_settings
        )
        btn_back = Button(
            text='返回',
            font_name='CustomFont',
            size_hint_y=None,
            height=max(48, Window.height * 0.06),
            font_size=max(18, Window.width * 0.03),
            on_press=lambda x: self.switch_screen('單字訓練')
        )
        layout.add_widget(btn_save)
        layout.add_widget(btn_clear)
        layout.add_widget(btn_back)
        scroll.add_widget(layout)
        self.add_widget(scroll)

        # Load existing settings
        api_key = get_api_key()
        api_model = get_api_model()
        if api_key:
            self.api_key_input.text = api_key
        if api_model and api_model != 'gemini-1.5-flash':
            self.api_model_input.text = api_model

        Window.bind(on_resize=self.on_window_resize)

    def on_window_resize(self, window, width, height):
        self.api_key_input.height = max(60, Window.height * 0.08)
        self.api_model_input.height = max(60, Window.height * 0.08)
        self.status_label.height = max(40, Window.height * 0.05)
        logging.info(f"SettingsScreen window resized: {width}x{height}")

    def switch_screen(self, screen_name):
        self.manager.current = screen_name
        logging.info(f"Switched from SettingsScreen to screen: {screen_name}")

    def save_settings(self, instance):
        api_key = self.api_key_input.text.strip()
        api_model = self.api_model_input.text.strip()
        if not api_key:
            self.status_label.text = '請輸入有效的 API 金鑰'
            return
        save_api_key(api_key)
        save_api_model(api_model)
        if configure_genai():
            self.status_label.text = 'API 設定已儲存並驗證成功'
        else:
            self.status_label.text = 'API 設定儲存成功，但驗證失敗，請檢查金鑰或模型是否正確'

    def clear_settings(self, instance):
        clear_api_key()
        clear_api_model()
        self.api_key_input.text = ''
        self.api_model_input.text = ''
        self.status_label.text = 'API 設定已清除'
        logging.info("API key and model cleared in SettingsScreen")

# ─── Word Screen ─────────────────────────────────────────────────────────
class WordScreen(Screen):
    def __init__(self, mode, **kw):
        super().__init__(**kw)
        self.mode = mode
        self.words = []
        self.idx = 0
        self.font_size_level = 'medium'

        root_layout = FloatLayout(size_hint=(1, 1))
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False, do_scroll_y=True)
        self.layout = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=max(15, Window.width * 0.02),
            padding=[max(20, Window.width * 0.03)] * 4
        )
        self.layout.bind(minimum_height=self.layout.setter('height'))

        self.lbl_progress = Label(
            text='',
            font_size=max(18, Window.width * 0.025),
            font_name='CustomFont',
            size_hint_y=None,
            height=max(40, Window.height * 0.05),
            halign='center',
            valign='middle'
        )
        self.lbl_progress.bind(size=lambda instance, value: setattr(self.lbl_progress, 'text_size', (self.lbl_progress.width * 0.9, None)))

        self.lbl_word = Label(
            font_size=40,
            font_name='CustomFont',
            size_hint_y=None,
            height=max(80, Window.height * 0.1),
            halign='center',
            valign='middle'
        )
        self.lbl_word.bind(size=lambda instance, value: setattr(self.lbl_word, 'text_size', (self.lbl_word.width * 0.9, None)))

        self.lbl_trans = Label(
            font_size=24,
            font_name='CustomFont',
            size_hint_y=None,
            height=max(100, Window.height * 0.12),
            halign='left',
            valign='middle',
            opacity=0
        )
        self.lbl_trans.bind(size=lambda instance, value: setattr(self.lbl_trans, 'text_size', (self.lbl_trans.width * 0.9, None)))

        self.lbl_example = Label(
            font_size=24,
            font_name='CustomFont',
            size_hint_y=None,
            height=max(120, Window.height * 0.15),
            halign='left',
            valign='top'
        )
        self.lbl_example.bind(size=lambda instance, value: setattr(self.lbl_example, 'text_size', (self.lbl_example.width * 0.9, None)))

        self.lbl_example_trans = Label(
            font_size=24,
            font_name='CustomFont',
            size_hint_y=None,
            height=max(140, Window.height * 0.18),
            halign='left',
            valign='top',
            opacity=0
        )
        self.lbl_example_trans.bind(size=lambda instance, value: setattr(self.lbl_example_trans, 'text_size', (self.lbl_example_trans.width * 0.9, None)))

        self.lbl_detail = Label(
            font_size=20,
            font_name='CustomFont',
            size_hint_y=None,
            height=max(80, Window.height * 0.1),
            halign='left',
            valign='middle'
        )
        self.lbl_detail.bind(size=lambda instance, value: setattr(self.lbl_detail, 'text_size', (self.lbl_detail.width * 0.9, None)))

        btn_audio = Button(
            text='播放',
            size_hint_y=None,
            height=max(48, Window.height * 0.06),
            font_name='CustomFont',
            font_size=max(18, Window.width * 0.03),
            on_press=lambda x: self.play()
        )
        btn_show = Button(
            text='顯示翻譯',
            size_hint_y=None,
            height=max(48, Window.height * 0.06),
            font_name='CustomFont',
            font_size=max(18, Window.width * 0.03),
            on_press=lambda x: self.show()
        )
        btn_mastered = Button(
            text='我會了',
            size_hint_y=None,
            height=max(48, Window.height * 0.06),
            font_name='CustomFont',
            font_size=max(18, Window.width * 0.03),
            on_press=lambda x: self.mastered()
        )
        
        btns = BoxLayout(
            size_hint_y=None,
            height=max(48, Window.height * 0.06),
            spacing=max(10, Window.width * 0.015)
        )
        for lvl in [('不熟', 1), ('模糊', 3), ('熟悉', 5)]:
            btns.add_widget(Button(
                text=lvl[0],
                font_name='CustomFont',
                size_hint_y=None,
                height=max(48, Window.height * 0.06),
                font_size=max(18, Window.width * 0.03),
                on_press=lambda x, l=lvl[1]: self.mark(l)
            ))
        
        btn_back = Button(
            text='返回',
            size_hint_y=None,
            height=max(48, Window.height * 0.06),
            font_name='CustomFont',
            font_size=max(18, Window.width * 0.03),
            on_press=lambda x: self.switch_screen('單字訓練')
        )

        self.layout.add_widget(self.lbl_progress)
        self.layout.add_widget(self.lbl_word)
        self.layout.add_widget(self.lbl_trans)
        self.layout.add_widget(btn_audio)
        self.layout.add_widget(self.lbl_example)
        self.layout.add_widget(self.lbl_example_trans)
        self.layout.add_widget(btn_show)
        self.layout.add_widget(self.lbl_detail)
        self.layout.add_widget(btn_mastered)
        self.layout.add_widget(btns)
        self.layout.add_widget(btn_back)
        scroll.add_widget(self.layout)
        root_layout.add_widget(scroll)

        font_size_btns = BoxLayout(
            orientation='horizontal',
            size_hint=(None, None),
            size=(120, 40),
            spacing=5,
            pos_hint={'right': 0.95, 'top': 0.95}
        )
        for size in [('大', 'large'), ('中', 'medium'), ('小', 'small')]:
            btn = Button(
                text=size[0],
                font_name='CustomFont',
                font_size=14,
                size_hint=(None, None),
                size=(40, 40),
                on_press=lambda x, s=size[1]: self.set_font_size(s)
            )
            font_size_btns.add_widget(btn)
        root_layout.add_widget(font_size_btns)

        self.add_widget(root_layout)
        Clock.schedule_once(lambda dt: self.load(), 0)
        Window.bind(on_resize=self.on_window_resize)

    def set_font_size(self, level):
        self.font_size_level = level
        self.adjust_font_sizes()
        logging.info(f"Font size set to: {level}")

    def on_window_resize(self, window, width, height):
        self.adjust_font_sizes()
        self.lbl_progress.height = max(40, Window.height * 0.05)
        self.lbl_word.height = max(80, Window.height * 0.1)
        self.lbl_trans.height = max(100, Window.height * 0.12)
        self.lbl_example.height = max(120, Window.height * 0.15)
        self.lbl_example_trans.height = max(140, Window.height * 0.18)
        self.lbl_detail.height = max(80, Window.height * 0.1)
        logging.info(f"WordScreen window resized: {width}x{height}")

    def on_pre_leave(self):
        if hasattr(play_word, 'current_sound') and play_word.current_sound:
            play_word.current_sound.stop()
        logging.info("Stopped audio on screen leave")

    def on_enter(self):
        self.load()

    def switch_screen(self, screen_name):
        self.manager.current = screen_name
        logging.info(f"Switched from WordScreen to screen: {screen_name}")

    def load(self):
        if not get_api_key():
            self.manager.current = '設置 API 金鑰'
            return
        if not configure_genai():
            self.manager.current = '設置 API 金鑰'
            return
        self.words = get_words_for_mode({'學習模式': 'learn', '複習模式': 'review', '已學習單字': 'mastered'}[self.mode])
        self.idx = 0
        self.show_word()

    def show_word(self):
        if self.idx >= len(self.words):
            self.lbl_word.text = '已完成'
            self.lbl_progress.text = f"{self.idx} / {len(self.words)}"
            self.lbl_trans.text = ''
            self.lbl_example.text = ''
            self.lbl_example_trans.text = ''
            self.lbl_detail.text = ''
            return
        
        row = self.words[self.idx]
        self.id = row[0]
        self.word = row[1]
        self.lbl_word.text = row[1]
        self.lbl_example.text = row[2] or ''
        self.lbl_trans.text = f"中文: {row[3] or ''}\n日文: {row[4] or ''}"
        self.lbl_example_trans.text = f"中文: {row[5] or ''}\n日文: {row[6] or ''}"
        pos = row[7] if row[7] else '未知'
        tense = row[8] if row[8] else '未知'
        self.lbl_detail.text = f"詞性: {pos}\n時態: {tense}"
        self.lbl_trans.opacity = 0
        self.lbl_example_trans.opacity = 0
        
        self.adjust_font_sizes()

        self.example_loaded = bool(row[2] and row[3] and row[4] and row[5] and row[6] and row[7] and row[8])
        if not self.example_loaded:
            try:
                example, zh_trans, ja_trans, zh_example_trans, ja_example_trans, pos, tense = fetch_word_details(self.word)
                conn = DatabaseManager.get_connection()
                cur = conn.cursor()
                cur.execute('''UPDATE words SET example=?, zh_translation=?, ja_translation=?, zh_example_translation=?, ja_example_translation=?, pos=?, tense=? WHERE id=?''',
                            (example, zh_trans, ja_trans, zh_example_trans, ja_example_trans, pos, tense, self.id))
                conn.commit()
                self.lbl_example.text = example or self.lbl_example.text
                self.lbl_trans.text = f"中文: {zh_trans or ''}\n日文: {ja_trans or ''}"
                self.lbl_example_trans.text = f"中文: {zh_example_trans or ''}\n日文: {ja_example_trans or ''}"
                self.lbl_detail.text = f"詞性: {pos}\n時態: {tense}"
            except Exception as e:
                logging.error(f"Failed to fetch details for word {self.word}: {e}")
                self.lbl_trans.text = "無法獲取翻譯（網路錯誤）"
        
        self.lbl_progress.text = f"{self.idx + 1} / {len(self.words)}"

    def adjust_font_sizes(self):
        base_scale = min(Window.width / 720, Window.height / 1280)
        font_sizes = {
            'large': {'word': dp(68), 'trans': dp(48), 'example': dp(48), 'example_trans': dp(48), 'detail': dp(44)},
            'medium': {'word': dp(58), 'trans': dp(38), 'example': dp(38), 'example_trans': dp(38), 'detail': dp(34)},
            'small': {'word': dp(32), 'trans': dp(20), 'example': dp(20), 'example_trans': dp(20), 'detail': dp(16)}
        }
        sizes = font_sizes[self.font_size_level]

        word_len = len(self.lbl_word.text)
        base_word_size = sizes['word'] * base_scale
        self.lbl_word.font_size = min(base_word_size, sizes['word'] if word_len < 15 else sizes['word'] * 0.8 if word_len < 30 else sizes['word'] * 0.6)

        trans_len = len(self.lbl_trans.text)
        base_trans_size = sizes['trans'] * base_scale
        self.lbl_trans.font_size = min(base_trans_size, sizes['trans'] if trans_len < 70 else sizes['trans'] * 0.8 if trans_len < 140 else sizes['trans'] * 0.7)

        example_len = len(self.lbl_example.text)
        base_example_size = sizes['example'] * base_scale
        self.lbl_example.font_size = min(base_example_size, sizes['example'] if example_len < 100 else sizes['example'] * 0.8 if example_len < 200 else sizes['example'] * 0.7)

        example_trans_len = len(self.lbl_example_trans.text)
        base_example_trans_size = sizes['example_trans'] * base_scale
        self.lbl_example_trans.font_size = min(base_example_trans_size, sizes['example_trans'] if example_trans_len < 140 else sizes['example_trans'] * 0.8 if example_trans_len < 280 else sizes['example_trans'] * 0.7)

        self.lbl_detail.font_size = min(sizes['detail'] * base_scale, sizes['detail'])

    def mark(self, lvl):
        conn = DatabaseManager.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT interval FROM words WHERE id = ?", (self.id,))
            current_interval = cur.fetchone()[0] or 1
            if lvl == 1:
                new_interval = 1
            elif lvl == 3:
                new_interval = current_interval + 1
            elif lvl == 5:
                new_interval = current_interval * 2
            else:
                new_interval = current_interval
            today = datetime.date.today().isoformat()
            next_review = (datetime.date.today() + datetime.timedelta(days=new_interval)).isoformat()
            cur.execute("UPDATE words SET familiarity=?, last_reviewed=?, interval=?, next_review=?, learned=1 WHERE id=?", 
                        (lvl, today, new_interval, next_review, self.id))
            conn.commit()
            logging.info(f"Marked word {self.word} with familiarity {lvl}, next review: {next_review}")
        except Exception as e:
            logging.error(f"Failed to update familiarity: {e}")
        self.idx += 1
        self.show_word()

    def show(self):
        self.lbl_trans.opacity = 1
        self.lbl_example_trans.opacity = 1

    def mastered(self):
        conn = DatabaseManager.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("UPDATE words SET mastered=1, learned=1 WHERE id=?", (self.id,))
            conn.commit()
            logging.info(f"Marked word {self.word} as mastered")
        except Exception as e:
            logging.error(f"Failed to mark as mastered: {e}")
        self.idx += 1
        self.show_word()

    def play(self):
        play_word(self.lbl_word.text)

# ─── Add Word Screen ─────────────────────────────────────────────────────────
class AddWordScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False, do_scroll_y=True)
        layout = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=max(15, Window.width * 0.02),
            padding=[max(20, Window.width * 0.03)] * 4
        )
        layout.bind(minimum_height=layout.setter('height'))

        self.input_word = TextInput(
            font_name='CustomFont',
            hint_text='請輸入單字（留空則從資料集獲取）',
            size_hint_y=None,
            height=max(60, Window.height * 0.08),
            font_size=max(18, Window.width * 0.03)
        )
        self.input_num_words = TextInput(
            font_name='CustomFont',
            hint_text='輸入要匯入的單字數量（預設10）',
            size_hint_y=None,
            height=max(60, Window.height * 0.08),
            font_size=max(18, Window.width * 0.03),
            input_filter='int'
        )
        self.input_example = TextInput(
            font_name='CustomFont',
            hint_text='請輸入例句',
            multiline=True,
            size_hint_y=None,
            height=max(100, Window.height * 0.12),
            font_size=max(18, Window.width * 0.03)
        )
        self.input_zh_translation = TextInput(
            font_name='CustomFont',
            hint_text='請輸入中文翻譯',
            size_hint_y=None,
            height=max(60, Window.height * 0.08),
            font_size=max(18, Window.width * 0.03)
        )
        self.input_ja_translation = TextInput(
            font_name='CustomFont',
            hint_text='請輸入日文翻譯',
            size_hint_y=None,
            height=max(60, Window.height * 0.08),
            font_size=max(18, Window.width * 0.03)
        )
        self.status_label = Label(
            text='',
            font_name='CustomFont',
            size_hint_y=None,
            height=max(40, Window.height * 0.05),
            font_size=max(16, Window.width * 0.025)
        )
        layout.add_widget(self.input_word)
        layout.add_widget(self.input_num_words)
        layout.add_widget(self.input_example)
        layout.add_widget(self.input_zh_translation)
        layout.add_widget(self.input_ja_translation)
        layout.add_widget(self.status_label)
        btn_add = Button(
            text='新增',
            font_name='CustomFont',
            size_hint_y=None,
            height=max(48, Window.height * 0.06),
            font_size=max(18, Window.width * 0.03),
            on_press=self.add_word
        )
        layout.add_widget(btn_add)
        btn_back = Button(
            text='返回',
            font_name='CustomFont',
            size_hint_y=None,
            height=max(48, Window.height * 0.06),
            font_size=max(18, Window.width * 0.03),
            on_press=lambda x: self.switch_screen('單字訓練')
        )
        layout.add_widget(btn_back)
        scroll.add_widget(layout)
        self.add_widget(scroll)
        Window.bind(on_resize=self.on_window_resize)

    def on_window_resize(self, window, width, height):
        self.input_word.height = max(60, Window.height * 0.08)
        self.input_num_words.height = max(60, Window.height * 0.08)
        self.input_example.height = max(100, Window.height * 0.12)
        self.input_zh_translation.height = max(60, Window.height * 0.08)
        self.input_ja_translation.height = max(60, Window.height * 0.08)
        self.status_label.height = max(40, Window.height * 0.05)
        logging.info(f"AddWordScreen window resized: {width}x{height}")

    def switch_screen(self, screen_name):
        self.manager.current = screen_name
        logging.info(f"Switched from AddWordScreen to screen: {screen_name}")

    def add_word(self, instance):
        if not get_api_key():
            self.manager.current = '設置 API 金鑰'
            return
        if not configure_genai():
            self.manager.current = '設置 API 金鑰'
            return
        self.status_label.text = '正在新增單字...'
        Clock.schedule_once(lambda dt: self._add_word_thread(), 0)

    def _add_word_thread(self):
        word = self.input_word.text.strip()
        num_words_input = self.input_num_words.text.strip()
        num_words = min(int(num_words_input), 100) if num_words_input.isdigit() else 10
        conn = DatabaseManager.get_connection()
        cur = conn.cursor()
        try:
            if word:
                if not is_valid_word(word):
                    self.status_label.text = '無效單字：請輸入僅含字母的單字'
                    return
                cur.execute("SELECT COUNT(*) FROM words WHERE word = ?", (word,))
                if cur.fetchone()[0] > 0:
                    self.status_label.text = f'單字 {word} 已存在'
                    return
                cur.execute('''INSERT INTO words (word, example, zh_translation, ja_translation, familiarity, learned, mastered, interval) 
                               VALUES (?, ?, ?, ?, 1, 0, 0, 1)''', 
                            (word, self.input_example.text, self.input_zh_translation.text, self.input_ja_translation.text))
                conn.commit()
                logging.info(f"Added word: {word}")
                self.status_label.text = f'成功新增單字：{word}'
            else:
                words_to_add = get_next_words(num_words)
                count = 0
                for w in words_to_add:
                    cur.execute("SELECT COUNT(*) FROM words WHERE word = ?", (w,))
                    if cur.fetchone()[0] > 0:
                        continue
                    try:
                        example, zh_trans, ja_trans, zh_example_trans, ja_example_trans, pos, tense = fetch_word_details(w)
                        cur.execute('''INSERT INTO words (word, example, zh_translation, ja_translation, zh_example_translation, ja_example_translation, pos, tense, familiarity, learned, mastered, interval) 
                                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, 0, 0, 1)''', 
                                    (w, example, zh_trans, ja_trans, zh_example_trans, ja_example_trans, pos, tense))
                        count += 1
                        logging.info(f"Added word from dataset: {w}")
                    except Exception as e:
                        logging.error(f"Failed to fetch details for word {w}, skipping: {e}")
                conn.commit()
                self.status_label.text = f'成功新增 {count} 個單字'
                logging.info(f"Added {count} words from dataset")
        except Exception as e:
            logging.error(f"Failed to add word: {e}")
            self.status_label.text = '新增失敗，請重試'

# ─── Help Screen ─────────────────────────────────────────────────────────
class HelpScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False, do_scroll_y=True)
        layout = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=max(15, Window.width * 0.02),
            padding=[max(20, Window.width * 0.03)] * 4
        )
        layout.bind(minimum_height=layout.setter('height'))

        help_text = '''
        歡迎使用單字訓練應用程式！
        - 學習模式：學習新單字
        - 複習模式：根據間隔重複系統複習單字
        - 已學習單字：查看已掌握的單字
        - 新增單字：新增單字（留空則從資料集獲取指定數量單字）
        - 匯入單字：從 vocabulary_export.csv 匯入單字
        - 匯出：將單字資料庫匯出為 CSV
        - 檢查資料庫：以彈出視窗查看資料庫統計資訊
        - 重製資料庫：清除所有單字（請先匯出以備份）
        - 設置 API 金鑰：輸入、更新或清除 Gemini API 金鑰和模型
        - 按「播放」按鈕播放單字發音
        - 點擊「顯示翻譯」查看單字和例句的中日文翻譯
        - 字體大小：右上角「大」「中」「小」按鈕調整字體
        '''
        lbl_help = Label(
            text=help_text,
            font_name='CustomFont',
            font_size=max(18, Window.width * 0.025),
            halign='left',
            valign='top',
            size_hint_y=None,
            height=max(600, Window.height * 0.7)
        )
        lbl_help.bind(size=lambda instance, value: setattr(lbl_help, 'text_size', (lbl_help.width * 0.9, None)))
        layout.add_widget(lbl_help)
        btn_back = Button(
            text='返回',
            size_hint_y=None,
            height=max(48, Window.height * 0.06),
            font_name='CustomFont',
            font_size=max(18, Window.width * 0.03),
            on_press=lambda x: self.switch_screen('單字訓練')
        )
        layout.add_widget(btn_back)
        scroll.add_widget(layout)
        self.add_widget(scroll)
        Window.bind(on_resize=self.on_window_resize)

    def on_window_resize(self, window, width, height):
        logging.info(f"HelpScreen window resized: {width}x{height}")

    def switch_screen(self, screen_name):
        self.manager.current = screen_name
        logging.info(f"Switched from HelpScreen to screen: {screen_name}")

# ─── App ─────────────────────────────────────────────────────
class VocabApp(App):
    def build_config(self, config):
        icon_path = os.path.join(BASE_DIR, 'icon.png')
        if os.path.exists(icon_path):
            logging.info(f"Set app icon: {icon_path}")
            config.setdefaults('kivy', {'window_icon': icon_path})
        else:
            logging.warning(f"Icon file missing: {icon_path}, using default icon")
            config.setdefaults('kivy', {'window_icon': ''})

    def build(self):
        create_database()
        init_settings_table()
        try:
            generate_top_words()
        except Exception as e:
            logging.error(f"Failed to generate top words list at startup: {e}")
            raise
        sm = ScreenManager()
        sm.add_widget(MainMenu(name='單字訓練'))
        sm.add_widget(WordScreen('學習模式', name='學習模式'))
        sm.add_widget(WordScreen('複習模式', name='複習模式'))
        sm.add_widget(WordScreen('已學習單字', name='已學習單字'))
        sm.add_widget(AddWordScreen(name='新增單字'))
        sm.add_widget(SettingsScreen(name='設置 API 金鑰'))
        sm.add_widget(HelpScreen(name='幫助'))
        return sm

    def on_stop(self):
        """Clean up resources when the app stops."""
        DatabaseManager.close_connection()
        manage_audio_cache()
        if hasattr(play_word, 'current_sound') and play_word.current_sound:
            play_word.current_sound.stop()
        logging.info("App stopped, resources cleaned up")

if __name__ == '__main__':
    try:
        VocabApp().run()
    except Exception as e:
        logging.error(f"Application failed: {e}")
        raise