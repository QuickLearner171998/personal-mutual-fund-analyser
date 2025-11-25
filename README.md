# MF Portfolio Bot

Personal mutual fund portfolio analyzer with AI-powered Q&A.

## Features
- 📁 CAS PDF upload and parsing (MF Central format)
- 📊 Portfolio dashboard with metrics and charts
- 💹 XIRR, CAGR, and allocation calculations
- 💾 **Local storage only** (JSON files + FAISS)
- 💬 AI Q&A (coming soon)

## Storage
**All data stored locally:**
- `data/portfolio.json` - Your holdings
- `data/transactions.json` - Transaction history
- `data/vector_store/` - FAISS embeddings for AI Q&A
- **No MongoDB, no cloud** - completely offline!

## Setup

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env and add your API keys
```

**Required API Keys:**
- `OPENAI_API_KEY` - For GPT-4o/o1 models
- `GOOGLE_API_KEY` - For Gemini fallback
- `PERPLEXITY_API_KEY` - For real-time market research

4. Run the app:
```bash
# Option 1: Using run script (fixes OpenMP crash)
./run.sh

# Option 2: Direct
streamlit run app.py

# Option 3: With environment fix
export KMP_DUPLICATE_LIB_OK=TRUE && streamlit run app.py
```

**Note:** If you get an OpenMP error, use `./run.sh` which includes the fix.

## Configuration

All parameters are configurable via `.env` file:

### LLM Models
```bash
PRIMARY_LLM_MODEL=gpt-4o              # Main model
REASONING_LLM_MODEL=o1-preview        # Complex reasoning
FALLBACK_LLM_MODEL=gemini-2.0-flash-exp  # Fallback
PERPLEXITY_MODEL=llama-3.1-sonar-large-128k-online
```

### Agent Controls
```bash
ENABLE_RAG=true                       # Semantic search
ENABLE_STREAMING=true                 # Token streaming
ENABLE_PORTFOLIO_AGENT=true
ENABLE_GOAL_AGENT=true
```

### Financial Assumptions
```bash
EXPECTED_EQUITY_RETURN=12             # Annual %
EXPECTED_DEBT_RETURN=7
MAX_EQUITY_ALLOCATION=80              # Portfolio %
```

See `.env.example` for all available options.

## Usage

1. **Upload CAS**: Go to "📁 Upload CAS" and upload your Consolidated Account Statement PDF
2. **View Dashboard**: Check "📊 Dashboard" for portfolio overview
3. **AI Q&A**: Ask questions about your portfolio (coming soon)

## Project Structure
```
mf_bot_ag/
├── app.py                 # Main Streamlit app
├── config.py              # Configuration
├── cas_import/            # CAS PDF parsing
├── enrichment/            # NAV fetching
├── calculations/          # Financial calculations
├── database/              # MongoDB operations
├── ui/                    # Streamlit UI components
├── agents/                # AI agents (WIP)
└── models/                # Data models
```

## Tech Stack
- **Frontend**: Streamlit, Plotly
- **PDF Parsing**: casparser
- **Calculations**: pyxirr, pandas
- **Database**: MongoDB
- **AI**: OpenAI GPT-4, Google Gemini (planned)
