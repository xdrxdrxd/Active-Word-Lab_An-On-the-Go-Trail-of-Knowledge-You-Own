# Ge-Vocapp

Ge-Vocapp is a vocabulary learning app that helps users remember English words more effectively using spaced repetition and example-based review. Built with Grok and powered by Gemini, it offers real-time translations and contextual example generation.

## 🔍 Features

- Spaced repetition memory system
- Simple interface with three response options: Familiar, Vague, Unfamiliar
- English-to-Chinese translation with example sentences
- Instant voice playback for words, cached playback for sentences
- Android-compatible (Python + Kivy)
- Clean UI with NotoSansSC-Regular font

## ⚙️ Powered By

- ✨ **Gemini API (Flash 2.0)**  
  Used to generate translations and example sentences.  
  *Note: API key is not included in this repository.*

- 📚 **English Word Frequency Dataset**  
  Sourced from [Rachael Tatman on Kaggle](https://www.kaggle.com/datasets/rtatman/english-word-frequency).  
  Licensed under [CC0 1.0 (Public Domain)](https://creativecommons.org/publicdomain/zero/1.0/).  
  The dataset is redistributed here for convenience.

- 🔤 **Font: NotoSansSC-Regular**  
  Provided by Google Noto Fonts.  
  Licensed under the [SIL Open Font License 1.1](https://github.com/notofonts/noto-cjk/blob/main/LICENSE).

## 🔐 API Key & Model Setup

To use Gemini API features, you must provide your own API key and preferred model (e.g., `gemini-1.5-flash`).  
These are securely stored in a local SQLite database (`vocabulary.db`) and are **not hardcoded** in the source code.

Keys can be set via the in-app settings screen, or manually inserted into the database (not recommended for general users).

## 🛠 Development Notes

- Written in Python using the Kivy framework
- Supports Android deployment
- Gemini API output is used for in-app, non-commercial educational purposes only

## 📄 License

This project is licensed under the MIT License.  
See `LICENSE` for details.

Additional licenses for third-party resources:

- `data/english-word-frequency.csv`: [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/)
- `assets/fonts/NotoSansSC-Regular.otf`: [SIL Open Font License 1.1](https://github.com/notofonts/noto-cjk/blob/main/LICENSE)
