# Glacious 🏔️

**Satellite-powered climate claim verification tool for Alpine journalism**

AlpineCheck uses satellite data, climate science, and AI to verify climate claims about the Alpine region. Upload suspicious claims, get instant verdicts backed by satellite evidence, and identify similar misinformation.

## Features

- 🛰️ **Satellite Data Analysis**: Real-time glacier, snow cover, and temperature data
- 🤖 **AI-Powered Processing**: Claude Sonnet 4 for claim parsing and summary generation
- 🗣️ **5-Language Support**: English, French, German, Italian, Slovenian
- 📊 **Interactive Visualizations**: Plotly charts and Folium maps
- 🔍 **Misinformation Matching**: TF-IDF similarity against known false claims
- 📄 **Report Generation**: Download verified analysis reports
- 🎮 **Demo Mode**: Test offline without API keys

## Project Structure

```
alpinecheck/
├── app.py                      # Main Streamlit application
├── requirements.txt            # Python dependencies
├── .env.example               # Environment template
├── pipeline/
│   ├── __init__.py
│   ├── claim_parser.py        # Claude API claim parsing
│   ├── data_loader.py         # Satellite + climate data simulation
│   ├── verdict_engine.py      # Scoring logic
│   ├── summarizer.py          # Claude API summary generation
│   ├── misinfo_matcher.py     # Climate misinformation matching
│   └── language.py            # i18n + language detection
├── data/
│   ├── glaciers.geojson       # RGI glacier sample outlines
│   └── misinfo_claims.json    # Climate misinformation database (auto-generated)
└── assets/
    └── (placeholder for before/after images)
```

## Installation

### 1. Clone or create the project directory

```bash
cd AlpineCheck
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

```bash
cp .env.example .env
```

Edit `.env` and add your Anthropic API key:
```
ANTHROPIC_API_KEY=sk-ant-...
```

Get your key from: https://console.anthropic.com/

### 5. Run the application

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`

## Usage

### 1. Select a language
Use the sidebar dropdown to choose your preferred language (5 options available).

### 2. Enter or load a claim
Enter a climate claim about the Alpine region, or load a pre-written example.

### 3. Click "Analyze claim"
The app will:
- Parse the claim using Claude AI
- Extract region, variable, time range, and language
- Load satellite data for that region
- Score the claim against the data
- Generate a multi-sentence journalist-ready summary

### 4. Review the verdict
Get a colored verdict badge:
- 🟢 **Supported**: Claim matches data trend
- 🟡 **Partially supported**: Claim direction matches but magnitude differs
- 🔴 **Contradicted**: Claim contradicts satellite evidence

### 5. Explore visualizations
Three tabs show:
- **Glacier Area**: 2000-2024 trend with 2000 baseline
- **Snow Cover**: Days of snow cover per year
- **Temperature**: Temperature anomaly vs. 1980-2010 baseline

### 6. Download report
Click "Full Report" → "Download Full Report" to get a text file with all analysis.

## Data Sources (Simulated for Demo)

- **Sentinel-2 / RGI v6**: Glacier outlines and area changes
- **MODIS MOD10A1**: Snow cover observations
- **EEAR-Clim**: Ground station temperature data
- **climate_fever**: Misinformation database

*All data shown is synthetic and generated from scientific literature values for demonstration purposes.*

## Supported Regions

- Mont Blanc (France, Italy)
- Swiss Alps (Switzerland)
- Aletsch Glacier (Switzerland)
- Dolomites (Italy)
- Austrian Alps (Austria)

## Supported Languages

- 🇬🇧 English
- 🇫🇷 Français
- 🇩🇪 Deutsch
- 🇮🇹 Italiano
- 🇸🇮 Slovenščina

## Supported Variables

- `glacier_area`: Glacier extent changes
- `snow_cover`: Days with snow cover
- `temperature`: Temperature anomalies
- `vegetation`: Vegetation zone shifts

## Architecture

### Pipeline Modules

**claim_parser.py**
- Calls Claude Sonnet 4 to extract structured data from free-text claims
- Detects language, region, variable, time range, and asserted direction
- Includes 6 pre-written example claims in 4+ languages

**data_loader.py**
- Generates realistic synthetic satellite data based on scientific literature
- Returns time series for glacier area, snow cover, and temperature
- Includes regional parameters for 5 Alpine regions

**verdict_engine.py**
- Compares claim direction with actual data trend
- Produces verdicts: "Supported", "Partially supported", "Contradicted"
- Calculates confidence scores and key statistics

**summarizer.py**
- Calls Claude Sonnet 4 to write 3-sentence summaries in target language
- Generates journalist-ready text for article inclusion
- Includes multilingual glossary of technical terms

**misinfo_matcher.py**
- TF-IDF cosine similarity against 20 known misinformation claims
- Auto-generates `misinfo_claims.json` on first run
- Returns top 3 similar claims with languages and verdicts

**language.py**
- Centralized i18n system with 5 languages
- 18+ UI strings translated
- Fallback to English if key not found

### Main App (app.py)

8 sections:
1. Claim input with example selector
2. Parsed claim display (4 metrics)
3. Verdict badge with confidence
4. Data visualizations (3 tabs)
5. AI-generated summary
6. Similar misinformation cards
7. Interactive Folium map
8. Downloadable full report

## API Models & Caching

- **Model**: `claude-sonnet-4-20250514`
- **Parsing**: Max 500 tokens
- **Summarization**: Max 300 tokens
- **Caching**: 1-hour TTL on data and API calls

## Demo Mode

Toggle **"📱 Demo Mode (offline)"** in the sidebar to:
- Use mock responses without API keys
- Test the UI offline
- Show the app at events without requiring API access

## Error Handling

- API key missing → Uses demo/default responses
- Invalid JSON parsing → Fallback to default parse
- Missing regions → Defaults to "Swiss Alps"
- Missing translations → Falls back to English

## Performance Notes

- Data loading is cached to avoid recomputation
- Plotly charts use minimal theme for fast rendering
- Folium map uses OpenStreetMap tiles
- TF-IDF vectorization is efficient for 20 claims

## Troubleshooting

**"API key not found"**
- Create `.env` file in project root
- Add `ANTHROPIC_API_KEY=your_key`
- Restart the app

**Map not displaying**
- Ensure streamlit-folium is installed
- Try refreshing the browser

**Missing misinformation data**
- Delete `data/misinfo_claims.json` to regenerate
- Ensure write permissions in `data/` folder

**Language strings not translating**
- Check language code is in ["en", "fr", "de", "it", "sl"]
- Verify JSON syntax in `pipeline/language.py`

## Development

### Adding a new region

1. Add to `REGIONAL_DATA` dict in `data_loader.py`:
```python
"New Region": {
    "glacier_area_2000": 100.0,
    "glacier_decline_pct": 0.30,
    "snow_days_2000": 140,
    "baseline_temp_c": 0.5,
}
```

2. Add marker to map in app.py

### Adding a new language

1. Add language code to `UI_STRINGS` in `pipeline/language.py`
2. Add language option to sidebar dropdown in `app.py`
3. Translate all keys in `UI_STRINGS[new_lang]`

### Adding a new integration

1. Create new module in `pipeline/`
2. Import in `app.py`
3. Add section to app with `st.subheader()`

## Limitations

- Data is simulated for hackathon demo (not real satellite data)
- 20 misinformation claims is representative sample, not exhaustive
- No image processing (before/after image placeholders only)
- Temperature data uses simplified anomaly model
- No real-time satellite API integration

## Future Enhancements

- Live Sentinel-2 API integration
- Real MODIS snow cover data
- Interactive threshold tuning
- Multi-claim batch analysis
- Export to standardized formats
- Community fact-checking integration

## License

MIT License - See LICENSE file for details

## Citation

If you use AlpineCheck for research, please cite:

```
AlpineCheck: A Satellite-Powered Climate Claim Verification Tool
Built for Alpine Journalism Hackathon, 2026
Powered by: Streamlit, Anthropic Claude API, Sentinel-2, MODIS
```

## Support

For issues, questions, or contributions:
1. Check the Troubleshooting section
2. Review module docstrings
3. Open an issue on GitHub

## Credits

- Built with [Streamlit](https://streamlit.io)
- AI by [Anthropic Claude](https://anthropic.com)
- Maps by [Folium](https://folium.readthedocs.io)
- Charts by [Plotly](https://plotly.com)
- Data inspired by scientific literature on Alpine climate

---

**Happy fact-checking! 🏔️**
