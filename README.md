#Ge-Vocapp

#Ge-Vocapp is a vocabulary learning app that helps users remember English words more effectively using spaced repetition and example-based review. Built with Python and Kivy, it offers real-time translations and contextual example generation in Chinese and Japanese, powered by the Gemini API.

🔍 Features





Spaced repetition memory system



Simple interface with three response options: Familiar, Vague, Unfamiliar



English-to-Chinese and English-to-Japanese translation with example sentences



Instant voice playback for words, cached playback for sentences



Android-compatible (Python + Kivy)



Clean UI with NotoSansSC-Regular font

⚙️ Powered By





✨ Gemini API (Flash 2.0)
Used to generate translations and example sentences.
Note: API key is not included in this repository.

📚 English Word Frequency Dataset





Sourced from Rachael Tatman on Kaggle.



Licensed under CC0 1.0 (Public Domain).



The dataset is redistributed here for convenience.

🔤 Font: NotoSansSC-Regular





Provided by Google Noto Fonts.



Licensed under the SIL Open Font License 1.1.

🔐 API Key & Model Setup

To use Gemini API features, you must provide your own API key and preferred model (e.g., gemini-1.5-flash). These are securely stored in a local SQLite database (vocabulary.db) and not hardcoded in the source code.

Setup Steps





Go to Google AI Studio to obtain a Gemini API key.



In the app, navigate to the "設置 API 金鑰" (Set API Key) screen.



Enter your API key and optional model (default: gemini-1.5-flash).



Click "儲存" (Save) to validate and save the key.

Keys can also be manually inserted into the database (not recommended for general users).

🛠 Installation & Deployment

Dependencies

Install the required Python packages:

pip install kivy gtts google-generativeai

Android Deployment





Install Buildozer:

pip install buildozer



Initialize Buildozer in the project directory:

buildozer init



Edit buildozer.spec to exclude sensitive files:

[app]
source.exclude_patterns = vocabulary.db, *.log, audio/, build/, dist/



Build the APK:

buildozer android debug

⚠️ Note: The Android deployment process (packaging into an app) has not been fully tested, and success is not guaranteed. Proceed with caution, and feel free to report any issues encountered during deployment.

📱 App Icon

The app currently uses the default Kivy icon. To customize the icon, add an icon.png (recommended size: 512x512 pixels) to the app/ directory and update buildozer.spec (for Android deployment):

[app]
icon = app/icon.png

🔒 Privacy Statement





Your Gemini API key is stored locally in vocabulary.db and is not uploaded to any server.



When using the Gemini API, your inputs (e.g., word queries) and generated responses may be logged by Google for abuse monitoring and legal disclosure, but they are not used for model training. For more details, see the Gemini API Additional Terms.

🛠 Development Notes





Written in Python using the Kivy framework.



Supports Android deployment.



Gemini API output is used for in-app, non-commercial educational purposes only.

📄 License

This project is licensed under the MIT License. See LICENSE for details.

Additional Licenses for Third-Party Resources





data/english-word-frequency.csv: CC0 1.0



assets/fonts/NotoSansSC-Regular.otf: SIL Open Font License 1.1

📩 Feedback & Support

If you encounter issues or have suggestions, please open an issue on the GitHub Issues page.



Copyright (c) 2025 xdrxdrxd
