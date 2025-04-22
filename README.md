# Ge-Vocapp

Ge-Vocapp is a vocabulary learning app that uses spaced repetition and example-based review to help learners remember English words more effectively. The app is built with Grok and integrates Google Gemini for real-time translation and example sentence generation.

## 🔍 Features

- Spaced repetition memory system
- Simple interface with three response options: Familiar, Vague, Unfamiliar
- English-to-Chinese translation with example sentences
- Instant voice playback for words and cached playback for sentences
- Supports Android devices via Python + Kivy
- Clean interface using NotoSansSC-Regular font

## ⚙️ Powered By

- ✨ **Gemini API (Flash 2.0)**  
  Used for generating translations and example sentences.  
  *Note: API key is not included in the public repository.*

- 📚 **English Word Frequency Dataset**  
  Sourced from [Rachael Tatman on Kaggle](https://www.kaggle.com/datasets/rtatman/english-word-frequency).  
  Licensed under [CC0 1.0 (Public Domain)](https://creativecommons.org/publicdomain/zero/1.0/).  
  The dataset is redistributed here for convenience.

- 🔤 **Font: NotoSansSC-Regular**  
  Provided by Google Noto Fonts, licensed under the [SIL Open Font License 1.1](https://github.com/notofonts/noto-cjk/blob/main/LICENSE).

## 🛠 Development Notes

- Developed in Python using the Kivy framework.
- API calls are handled securely (API key stored locally via `.env`, excluded from Git).
- Gemini outputs are used solely for in-app, non-commercial language learning purposes.

## 📄 License

This project is licensed under the MIT License.  
See `LICENSE` for more information.

Additional licenses for third-party resources:
- `data/english-word-frequency.csv`: [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/)
- `assets/fonts/NotoSansSC-Regular.otf`: [SIL Open Font License 1.1](https://github.com/notofonts/noto-cjk/blob/main/LICENSE)

---

Feel free to contribute or suggest improvements!
