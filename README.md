# QuizForge AI

QuizForge AI turns uploaded study material into focused multiple-choice practice.

## Features

- PDF, DOCX and TXT material extraction
- Gemini-powered question generation
- Local fallback when Gemini is unavailable
- Difficulty selection
- Topic selection
- Practice mode
- Analytics and topic performance
- Detailed answer review
- Streamlit interface
- GitHub / Streamlit Community Cloud friendly structure

## Local run

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
pip install -r requirements.txt
```

Create `.env` from `.env.example` and add your Gemini API key.

Then:

```bash
streamlit run app.py
```

## Deployment

For Streamlit Community Cloud, deploy this repository and add `GEMINI_API_KEY` under the app's Secrets settings. The application also works without the key using its local fallback generator.

## Gemini model

The default model is `gemini-3.8-flash`. It can be changed through `GEMINI_MODEL`.
