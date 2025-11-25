# MF Portfolio Analyzer

AI-powered mutual fund portfolio analyzer with comprehensive analytics, SIP tracking, and broker analysis.

## 🎯 Features

### Core Functionality
- 📁 **MF Central Data Import** - Upload 3 JSON files from MF Central
- 📊 **Enhanced Dashboard** - Portfolio overview with XIRR, CAGR, and detailed analytics
- 💰 **SIP Analytics** - Track active SIPs, upcoming installments, and performance
- 🤝 **Broker Analysis** - Investment breakdown by broker/intermediary
- 📈 **Fund Aggregation** - Automatically merge duplicate funds across folios
- 💬 **AI Q&A** - Ask questions about your portfolio using natural language
- 💾 **Local Storage** - All data stored locally in JSON files (no cloud/database)

### Analytics
- **XIRR Calculation** - Fund-level and portfolio-wide XIRR
- **CAGR Analysis** - Period-wise CAGR (1Y, 3Y, 5Y)
- **Asset Allocation** - Detailed breakdown by type and category
- **Performance Tracking** - Top/bottom performers with charts
- **SIP Returns** - Dedicated SIP performance analysis

## 🚀 Quick Start

### 1. Setup

```bash
# Clone repository
git clone <repo-url>
cd personal-mutual-fund-analyser

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your API keys
```

### 2. Test the Parser

```bash
# Run test suite
python main.py
```

Expected output:
```
✅ PASS - Configuration
✅ PASS - MF Central Parser
✅ PASS - Portfolio Storage
✅ PASS - Calculations

Passed: 4/4
```

### 3. Run the App

```bash
streamlit run app.py
```

The app will be available at: http://localhost:8501

## 📥 Data Upload

### Required Files from MF Central

1. **CONSOLIDATED PORTFOLIO STATEMENT**
   - Download from: MF Central → Portfolio → Consolidated Portfolio Statement
   - Extract ZIP file
   - Upload: `CurrentValuationAS*.json`

2. **TRANSACTION DETAILS STATEMENT**
   - Download from: MF Central → Transactions → Transaction Details Statement
   - Extract ZIP file
   - Upload: `AS*.json`

3. **Detailed Report with XIRR**
   - Download from: MF Central → Reports → Detailed Report
   - Upload: `*IMBPF*.json`

### Upload Process

1. Go to "📁 Upload MF Central Data"
2. Upload all 3 JSON files
3. Click "Process Files"
4. View your portfolio in the Dashboard

## 🔧 Configuration

### API Keys (Required)

```bash
# .env file
OPENAI_API_KEY=sk-...           # For GPT-4o/GPT-4o-mini
GOOGLE_API_KEY=...              # For Gemini fallback
PERPLEXITY_API_KEY=pplx-...     # For market research
```

### LLM Models

```bash
PRIMARY_LLM_MODEL=gpt-5                    # General tasks with reasoning
RAG_LLM_MODEL=gpt-4.1-mini                # Fast RAG queries
REASONING_LLM_MODEL=gpt-5                 # Complex thinking
FALLBACK_LLM_MODEL=gemini-2.0-flash-exp   # Fallback
PERPLEXITY_MODEL=sonar-pro                # Market research
```

See [docs/LLM_USAGE.md](docs/LLM_USAGE.md) for detailed LLM documentation.

## 📊 Dashboard Features

### Main Dashboard
- **Portfolio Overview**: Total value, invested amount, gain/loss, XIRR
- **View Toggle**: Switch between aggregated and individual folio views
- **Holdings Table**: Enhanced with XIRR, broker, and aggregation columns
- **Top Performers**: XIRR-based ranking with interactive charts
- **Asset Allocation**: Pie chart breakdown by fund type
- **Broker Analysis**: Investment distribution across brokers
- **Category Performance**: Type-wise performance summary

### SIP Analytics
- **SIP Overview**: Active count, monthly outflow, total invested
- **Upcoming Calendar**: Next 30 days installment schedule
- **SIP Details**: Complete SIP information table
- **Performance Analysis**: SIP-specific XIRR and returns
- **Contribution Timeline**: Monthly SIP investment chart

## 🤖 AI Q&A (Multi-Agent System)

Ask questions like:
- "What is my total investment?"
- "Show me my top performing funds"
- "Which broker has my best funds?"
- "When is my next SIP installment?"
- "Compare HDFC Flexi Cap vs ICICI Flexi Cap"
- "How much to invest for retirement?"

### Available Agents
- **Portfolio Agent** - Portfolio-specific queries (uses RAG)
- **Market Agent** - Real-time market data (uses Perplexity)
- **Strategy Agent** - Investment recommendations
- **Comparison Agent** - Fund comparisons
- **Goal Agent** - Financial goal planning
- **Coordinator** - Routes queries to appropriate agent

## 📁 Project Structure

```
personal-mutual-fund-analyser/
├── app.py                          # Main Streamlit app
├── main.py                         # Test suite
├── config.py                       # Configuration
│
├── cas_import/
│   └── mf_central_parser.py        # MF Central JSON parser
│
├── models/
│   └── portfolio.py                # Enhanced data models
│
├── database/
│   └── json_store.py               # Local JSON storage
│
├── calculations/
│   └── returns.py                  # XIRR, CAGR, SIP returns
│
├── ui/
│   ├── dashboard.py                # Enhanced dashboard
│   ├── sip_analytics.py            # SIP analytics
│   ├── cas_upload.py               # MF Central upload
│   └── chat.py                     # AI Q&A interface
│
├── agents/
│   ├── coordinator.py              # Query routing
│   ├── portfolio_agent.py          # Portfolio Q&A
│   ├── market_agent.py             # Market research
│   ├── strategy_agent.py           # Investment advice
│   ├── comparison_agent.py         # Fund comparison
│   └── goal_agent.py               # Goal planning
│
├── llm/
│   ├── llm_wrapper.py              # Unified LLM interface
│   └── prompts.py                  # Agent prompts
│
├── vector_db/
│   ├── faiss_store.py              # Vector storage
│   └── portfolio_indexer.py        # Portfolio indexing
│
└── docs/
    ├── data_extraction_guide.md    # Data extraction details
    ├── LLM_USAGE.md                # LLM usage documentation
    ├── REVAMP_SUMMARY.md           # Implementation summary
    └── CLEANUP.md                  # Cleanup summary
```

## 🧪 Testing

```bash
# Run all tests
python main.py

# Tests include:
# - Configuration validation
# - MF Central parser
# - Portfolio storage
# - Financial calculations
```

## 📚 Documentation

- **[Data Extraction Guide](docs/data_extraction_guide.md)** - Detailed data extraction methodology
- **[LLM Usage](docs/LLM_USAGE.md)** - LLM models and usage patterns
- **[Implementation Summary](docs/REVAMP_SUMMARY.md)** - Complete implementation details
- **[Cleanup Summary](docs/CLEANUP.md)** - Removed files and cleanup

## 🛠️ Tech Stack

- **Frontend**: Streamlit, Plotly
- **Data Processing**: Pandas, NumPy
- **Calculations**: pyxirr (XIRR), custom CAGR
- **Storage**: JSON files (local)
- **Vector DB**: FAISS (local)
- **LLMs**: 
  - OpenAI GPT-5 (primary with reasoning)
  - OpenAI GPT-4.1-mini (RAG)
  - OpenAI GPT-5 (reasoning)
  - Google Gemini 2.0 Flash (fallback)
  - Perplexity Sonar Pro (market research)

## 📈 Sample Results

From test data:
- **Portfolio Value**: ₹55.27 Lakhs
- **Total Invested**: ₹42.50 Lakhs
- **Total Gain**: ₹12.77 Lakhs (30.06%)
- **Portfolio XIRR**: 16.79%
- **Funds**: 26 (24 after aggregation)
- **Active SIPs**: 11
- **Brokers**: 5

## 🔒 Privacy

- **100% Local**: All data stored locally in `./data/` directory
- **No Cloud**: No MongoDB, no external databases
- **No Uploads**: Data never leaves your machine
- **API Calls**: Only for LLM queries (OpenAI, Google, Perplexity)

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- MF Central for data sources
- OpenAI for GPT models
- Google for Gemini
- Perplexity for market research API
- Streamlit for the amazing framework

---

**Built with ❤️ for Indian mutual fund investors**
