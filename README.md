# Kuku Promo Finder – AI-Powered Promo Clip Detection

## 🚀 Project Overview

Kuku Promo Finder is an AI-powered application that automatically identifies and ranks promotional clips from episodic screenplays.

The system analyzes screenplay content to find potential promo segments based on their emotional impact, hook strength, cliffhanger potential, narrative coherence, and suitability for standalone promotional content.

## 🌐 Prototype Link

**Live Prototype:** [Open Kuku Promo Finder](https://kuku-promo-finder-lexrirmavpi3xrw8xtgcyc.streamlit.app/))

## ✨ Key Features

- **Multiple Input Options:** Upload individual TXT files, ZIP files containing screenplays, or paste screenplay text directly.
- **Screenplay Parsing:** Extracts dialogue, scenes, and relevant screenplay information.
- **Candidate Generation:** Identifies potential promotional segments from screenplay content.
- **AI-Based Evaluation:** Uses the Groq API to evaluate candidates across multiple quality parameters.
- **Promo Ranking:** Ranks candidates based on their evaluation scores.
- **Selected Promos:** Identifies promising promotional clips.
- **Downloadable Results:** Provides JSON and CSV outputs for analysis.

## ⚙️ Workflow

1. Upload screenplay files or paste screenplay text.
2. Parse screenplay content into structured data.
3. Generate potential promotional clip candidates.
4. Evaluate candidates using the Groq LLM.
5. Calculate rankings and identify selected promos.
6. View and download the results.

## 🛠️ Tech Stack

- **Programming Language:** Python
- **Frontend:** Streamlit
- **LLM Provider:** Groq API
- **Data Validation:** Pydantic
- **Data Formats:** JSON, CSV, TXT
- **Libraries:** Pandas and other Python dependencies

## 📊 Implementation Results

The current implementation was tested on 50 screenplay episodes.

| Metric | Result |
|---|---:|
| Episodes Parsed | 50 |
| Candidates Generated | 252 |
| Successfully Evaluated Candidates | 100|

**Note:** Due to Groq API token limits, only 100 candidates were successfully evaluated in this run. Precision and recall have not been measured because a complete human-labelled validation dataset is not available.

## 📁 Project Structure

```text
kuku-promo-finder/
│
├── app.py
├── parser.py
├── candidate_generator.py
├── llm_evaluator.py
├── requirements.txt
├── .env.example
├── README.md
│
└── data/
    ├── raw/
    ├── processed/
    └── outputs/
```

## 💻 Installation and Setup

**1. Clone the repository**

```bash
git clone https://github.com/YOUR_USERNAME/kuku-promo-finder.git
cd kuku-promo-finder
```

**2. Create a virtual environment**

```bash
python -m venv .venv
```

**3. Activate the environment**

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
source .venv/bin/activate
```

**4. Install dependencies**

```bash
pip install -r requirements.txt
```

**5. Configure the Groq API key**

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key
```

**6. Run the application**

```bash
streamlit run app.py
```

The application will open in your browser.

## ⚠️ Limitations and Future Improvements

- Improve candidate generation to reduce unnecessary segments.
- Optimize LLM API usage and handle rate limits.
- Improve evaluation consistency and ranking accuracy.
- Introduce human-labelled validation data to measure precision and recall.
- Further improve standalone comprehensibility and narrative coherence evaluation.

## 👨‍💻 Author

**Mayur Arya**

---

