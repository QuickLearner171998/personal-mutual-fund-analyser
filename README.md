# MF Portfolio Analyzer

AI-powered mutual fund portfolio analyzer with comprehensive analytics, SIP tracking, and broker analysis.

## 🎯 Features

- 📁 **MF Central Data Import** - Upload 3 files (Excel + 2 JSONs) from MF Central
- 📊 **Portfolio Dashboard** - Complete overview with XIRR, gains, and holdings
- 💰 **SIP Analytics** - Track active SIPs and upcoming installments
- 💬 **AI Q&A** - Ask questions about your portfolio using natural language
- 🤝 **Broker Analysis** - Investment breakdown by broker/intermediary

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install --break-system-packages -r requirements.txt
```

### 2. Run the Application

```bash
./run.sh
```

The app will be available at: **http://localhost:5000**

## 📥 Upload Your Data

1. Go to **Upload Data** page
2. Upload 3 files from MF Central:
   - **Excel Report**: `cas_detailed_report_*.xlsx`
   - **Transaction JSON**: `AS*.json`
   - **XIRR JSON**: `*IMBPF*.json`
3. Click "Upload and Process Files"
4. View your dashboard!

## 🏗️ Architecture

### Single Flask Server
- **Flask** handles all routes and rendering
- **Server-side rendering** with Jinja2 templates
- **Direct integration** with existing backend code:
  - `core/unified_processor.py` - Data processing
  - `database/json_store.py` - Local storage
  - `agents/orchestrator.py` - AI Q&A

### Project Structure

```
personal-mutual-fund-analyser/
├── frontend/
│   ├── app.py                      # Main Flask application
│   ├── templates/
│   │   ├── base.html              # Base template
│   │   ├── dashboard.html         # Dashboard page
│   │   ├── upload.html            # Upload page
│   │   ├── sip_analytics.html     # SIP analytics
│   │   └── chat.html              # AI chat
│   └── static/
│       ├── css/style.css          # Modern CSS
│       └── js/                    # Minimal JS
│
├── core/                           # Data processing
├── database/                       # JSON storage
├── agents/                         # AI agents
├── api_server.py                   # FastAPI (optional, for API-only use)
└── run.sh                          # Start script
```

## 💻 Technology Stack

### Backend
- **Flask** - Web framework
- **Python** - Core logic
- Existing backend components (processors, database, agents)

### Frontend
- **Jinja2** - Template engine
- **HTML/CSS** - Modern, responsive design
- **Minimal JavaScript** - Only for form submissions

## 🧪 Testing (Optional API)

If you want to use the REST API:

```bash
# Start FastAPI backend
./run_backend.sh

# Test endpoints
curl http://localhost:8000/api/health
curl http://localhost:8000/api/portfolio/summary

# API Docs
open http://localhost:8000/docs
```

## 📊 Features In Detail

### Dashboard
- Total portfolio value and invested amount
- Gain/loss with percentage
- Portfolio XIRR
- Complete holdings table
- Broker-wise breakdown

### SIP Analytics
- Active SIPs count
- Monthly outflow
- Upcoming installments (next 30 days)
- SIP details with broker info

### AI Q&A
- Ask questions about your portfolio
- Multi-agent system for intelligent responses
- Chat history
- Quick question templates

## 🔒 Privacy

- **100% Local** - All data stored in `./data/` directory
- **No Cloud** - No external databases
- **No Uploads** - Data never leaves your machine
- **API Calls** - Only for LLM queries (OpenAI, Google, Perplexity)

## 📝 Configuration

Create a `.env` file with your API keys:

```bash
# LLM API Keys
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...
PERPLEXITY_API_KEY=pplx-...

# Models
PRIMARY_LLM_MODEL=gpt-4o
FALLBACK_LLM_MODEL=gemini-2.0-flash-exp
```

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

---

**Built with ❤️ for Indian mutual fund investors**
