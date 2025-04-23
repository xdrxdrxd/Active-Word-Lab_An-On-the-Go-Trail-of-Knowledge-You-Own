# Active Word Lab: An On-the-Go Trail of Knowledge You Own

Active Word Lab: An On-the-Go Trail of Knowledge You Own is a vocabulary learning app that helps users remember English words more effectively using spaced repetition and example-based review. Built with Python and Kivy, the app was initially generated using Grok and later extended and customized. It offers real-time translations and contextual example sentence generation in Chinese and Japanese, powered by the Gemini API.

## 🔍 Features

- Advanced spaced repetition memory system  
- Navigable, intuitive interface with three response options: **Familiar**, **Vague**, **Unfamiliar**  
- Optimized English-to-Chinese and English-to-Japanese translations with example sentences  
- Native voice playback for words and cached playback for sentences  
- Tailored for Android compatibility (Python + Kivy)  
- Optimal UI with NotoSansSC-Regular font  
- Key features designed for efficient language learning  
- Yield measurable progress through personalized repetition schedules  
- Optimized for both beginner and advanced learners

## ⚙️ Powered By

### ✨ Gemini API (Flash 2.0)
Used to generate translations and example sentences.  
**Note:** API key is not included in this repository.

### 📚 English Word Frequency Dataset
- Sourced from [Rachael Tatman on Kaggle](https://www.kaggle.com/datasets/rtatman/english-word-frequency)  
- Licensed under [CC0 1.0 (Public Domain)](https://creativecommons.org/publicdomain/zero/1.0/)  
- The dataset is redistributed here for convenience.

### 🔤 Font: NotoSansSC-Regular
- Provided by [Google Noto Fonts](https://notofonts.github.io)  
- Licensed under the [SIL Open Font License 1.1](https://github.com/notofonts/noto-cjk/blob/main/LICENSE)

## 🔐 API Key & Model Setup

To use Gemini API features, you must provide your own API key and preferred model (e.g., `gemini-1.5-flash`). These are securely stored in a local SQLite database (`vocabulary.db`) and **not hardcoded** in the source code.

### Setup Steps

1. Go to [Google AI Studio](https://aistudio.google.com/) to obtain a Gemini API key.  
2. In the app, navigate to the **"設置 API 金鑰" (Set API Key)** screen.  
3. Enter your API key and optional model (default: `gemini-1.5-flash`).  
4. Click **"儲存" (Save)** to validate and save the key.  

> Keys can also be manually inserted into the database (not recommended for general users).

## 🛠 Installation & Deployment

### Dependencies

Install the required Python packages:

```bash
pip install kivy gtts google-generativeai
```

### Android Deployment

1. Install Buildozer:

```bash
pip install buildozer
```

2. Initialize Buildozer in the project directory:

```bash
buildozer init
```

3. Edit `buildozer.spec` to exclude sensitive files:

```ini
[app]
source.exclude_patterns = vocabulary.db, *.log, audio/, build/, dist/
```

4. Build the APK:

```bash
buildozer android debug
```

> ⚠️ **Note:** The Android deployment process (packaging into an app) has not been fully tested, and success is not guaranteed. Proceed with caution, and feel free to report any issues encountered during deployment.

## 📱 App Icon

The app currently uses the default Kivy icon.  
To customize the icon:

1. Add an `icon.png` (recommended size: 512x512 pixels) to the `app/` directory  
2. Update `buildozer.spec`:

```ini
[app]
icon.filename = app/icon.png
```

## 🔒 Privacy Statement

- Your Gemini API key is stored locally in `vocabulary.db` and is **not uploaded** to any server.  
- When using the Gemini API, your inputs (e.g., word queries) and generated responses **may be logged by Google** for abuse monitoring and legal compliance. They are **not used for model training**.  
  See the Gemini API [Additional Terms](https://ai.google.dev/terms) for more details.

## 🛠 Development Notes

- Written in Python using the Kivy framework  
- Supports Android deployment  
- Gemini API output is used for in-app, **non-commercial educational purposes only**

## 📄 License

This project is licensed under the **MIT License**. See [`LICENSE`](LICENSE) for details.

### Additional Licenses for Third-Party Resources

- `data/english-word-frequency.csv`: [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/)  
- `assets/fonts/NotoSansSC-Regular.otf`: [SIL Open Font License 1.1](https://github.com/notofonts/noto-cjk/blob/main/LICENSE)

## 📩 Feedback & Support

If you encounter issues or have suggestions, please open an issue on the GitHub [Issues page](../../issues).

---

© 2025 xdrxdrxd
