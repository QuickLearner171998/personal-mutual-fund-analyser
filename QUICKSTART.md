# Quick Start Guide

## Running the Application

### Single Command

```bash
./run.sh
```

Visit: **http://localhost:5000**

That's it! The app will start and you can:
1. Upload your MF Central files
2. View dashboard
3. Analyze SIPs
4. Ask AI questions

## Troubleshooting

### If you get import errors:

```bash
pip install --break-system-packages flask requests
```

### If port 5000 is busy:

Edit `frontend/app.py` and change:
```python
app.run(host='0.0.0.0', port=5001, debug=True)  # Use different port
```

### Check if it's working:

```bash
cd frontend
python -c "from app import app; print('✅ App OK')"
```

## File Upload Requirements

You need 3 files from MF Central:

1. **Excel Report** (`.xlsx`)
   - MF Central → Reports → Detailed Report

2. **Transaction JSON** (`AS*.json`)
   - MF Central → Transactions → Transaction Details Statement
   - Extract from ZIP

3. **XIRR JSON** (`*IMBPF*.json`)
   - Same as Excel report download
   - Extract from ZIP

## Features

- 📊 Dashboard with portfolio overview
- 💰 SIP analytics and upcoming installments
- 💬 AI Q&A for portfolio queries
- 🎨 Modern UI with dark theme
- 🔒 100% local - no cloud storage

## Support

If you encounter issues:
1. Check all three files are uploaded
2. Ensure .env file has API keys
3. Check terminal for error messages
