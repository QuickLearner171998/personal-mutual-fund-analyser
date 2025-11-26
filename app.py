"""
Flask Application for MF Portfolio Analyzer
Single server handling all functionality
"""
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import os
import sys

# Import centralized logger FIRST
from utils.logger import get_logger

logger = get_logger(__name__)

from core.unified_processor import process_mf_central_complete
from database.json_store import PortfolioStore
from vector_db.portfolio_indexer import index_portfolio_data
from agents.orchestrator import MultiAgentOrchestrator

app = Flask(__name__, template_folder='frontend/templates', static_folder='frontend/static')
app.config['SECRET_KEY'] = os.urandom(24)

logger.info("Initializing Flask application")

# Initialize components
store = PortfolioStore()
orchestrator = MultiAgentOrchestrator()

logger.info("Components initialized successfully")

# Upload directory
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.route('/')
def index():
    """Home page - redirect to dashboard"""
    return redirect(url_for('dashboard'))


@app.route('/dashboard')
def dashboard():
    """Portfolio dashboard"""
    try:
        portfolio = store.get_portfolio()
        if not portfolio:
            return render_template('dashboard.html', summary=None, holdings=[])
        
        holdings = portfolio.get('holdings', [])
        # Sort by current value
        holdings = sorted(holdings, key=lambda x: x.get('current_value', 0), reverse=True)
        
        return render_template('dashboard.html', summary=portfolio, holdings=holdings)
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return render_template('dashboard.html', summary=None, holdings=[])


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    """File upload page"""
    if request.method == 'POST':
        excel_file = request.files.get('excel_file')
        transaction_json = request.files.get('transaction_json')
        xirr_json = request.files.get('xirr_json')
        
        if not all([excel_file, transaction_json, xirr_json]):
            flash('Please upload all 3 required files', 'error')
            return redirect(url_for('upload'))
        
        try:
            # Save files
            import shutil
            excel_path = os.path.join(UPLOAD_DIR, excel_file.filename)
            transaction_path = os.path.join(UPLOAD_DIR, transaction_json.filename)
            xirr_path = os.path.join(UPLOAD_DIR, xirr_json.filename)
            
            excel_file.save(excel_path)
            transaction_json.save(transaction_path)
            xirr_json.save(xirr_path)
            
            # Process files
            portfolio_data = process_mf_central_complete(
                excel_path=excel_path,
                transaction_json_path=transaction_path,
                xirr_json_path=xirr_path
            )
            
            # Save to database
            store.save_complete_data(
                portfolio=portfolio_data,
                transactions=[],
                sips=portfolio_data.get('active_sips', []),
                broker_info=portfolio_data.get('broker_info', {}),
                aggregation_map={}
            )
            
            # Index for vector search
            try:
                logger.info("Starting vector indexing")
                index_portfolio_data(portfolio_data)
                logger.info("Vector indexing completed")
            except Exception as e:
                logger.warning(f"Vector indexing failed: {e}")
            
            flash(f'Successfully processed {portfolio_data.get("num_funds", 0)} funds!', 'success')
            return redirect(url_for('dashboard'))
        
        except Exception as e:
            flash(f'Upload failed: {str(e)}', 'error')
            return redirect(url_for('upload'))
    
    return render_template('upload.html')


@app.route('/sip-analytics')
def sip_analytics():
    """SIP analytics page"""
    try:
        portfolio = store.get_portfolio()
        sips = store.get_sips()
        
        if not portfolio or not sips:
            return render_template('sip_analytics.html', analytics=None, sips=[], upcoming={'upcoming_sips': [], 'count': 0, 'total_amount': 0})
        
        # Calculate analytics
        total_sips = len(sips)
        active_sips = [s for s in sips if s.get('is_active', True)]
        monthly_outflow = sum(s.get('sip_amount', 0) for s in active_sips if s.get('frequency', '').lower() == 'monthly')
        
        # Calculate upcoming SIPs
        from datetime import datetime, timedelta
        today = datetime.now()
        upcoming = []
        total_amount = 0
        
        for sip in active_sips:
            next_date = sip.get('next_installment_date')
            if next_date:
                try:
                    next_date_dt = datetime.strptime(next_date, '%Y-%m-%d')
                    days_until = (next_date_dt - today).days
                    
                    if 0 <= days_until <= 30:
                        upcoming.append({
                            'scheme_name': sip.get('scheme_name', ''),
                            'sip_amount': sip.get('sip_amount', 0),
                            'date': next_date,
                            'days_until': days_until,
                            'broker': sip.get('broker', 'Unknown')
                        })
                        total_amount += sip.get('sip_amount', 0)
                except:
                    pass
        
        upcoming.sort(key=lambda x: x['days_until'])
        
        analytics = {
            'data': {
                'total_sips': total_sips,
                'active_sips': len(active_sips),
                'monthly_outflow': monthly_outflow,
                'avg_sip_amount': monthly_outflow / len(active_sips) if active_sips else 0
            }
        }
        
        upcoming_data = {
            'upcoming_sips': upcoming,
            'count': len(upcoming),
            'total_amount': total_amount
        }
        
        return render_template('sip_analytics.html', analytics=analytics, sips=sips, upcoming=upcoming_data)
    
    except Exception as e:
        flash(f'Error loading SIP analytics: {str(e)}', 'error')
        return render_template('sip_analytics.html', analytics=None, sips=[], upcoming={'upcoming_sips': [], 'count': 0, 'total_amount': 0})


@app.route('/chat', methods=['GET', 'POST'])
def chat():
    """AI Q&A chat interface"""
    if request.method == 'POST':
        message = request.form.get('message')
        if message:
            try:
                logger.info(f"Received chat message: '{message}'")
                
                # Check if portfolio data exists
                portfolio = store.get_portfolio()
                if not portfolio:
                    logger.warning("No portfolio data found")
                    return jsonify({'error': 'No portfolio data found. Please upload files first.'}), 404
                
                logger.info("Processing query through orchestrator")
                # Get response from AI
                response = orchestrator.process_query(message)
                
                logger.info(f"Response generated: {len(response)} characters")
                
                # Save to history (in-memory for now)
                if not hasattr(app, 'chat_history'):
                    app.chat_history = []
                
                from datetime import datetime
                app.chat_history.append({
                    'role': 'user',
                    'content': message,
                    'timestamp': datetime.now()
                })
                app.chat_history.append({
                    'role': 'assistant',
                    'content': response,
                    'timestamp': datetime.now()
                })
                
                logger.info("Chat response sent successfully")
                return jsonify({'response': response})
            except Exception as e:
                logger.error(f"Chat error: {str(e)}")
                return jsonify({'error': str(e)}), 500
    
    # Get chat history
    history = getattr(app, 'chat_history', [])
    return render_template('chat.html', history=history)


# Template filters
@app.template_filter('currency')
def currency_filter(value):
    """Format as Indian currency (Lakhs/Crores)"""
    if value is None:
        return '₹0'
    
    try:
        value = float(value)
    except (ValueError, TypeError):
        return '₹0'
        
    def format_indian(n):
        s = str(int(n))
        if len(s) <= 3:
            return s
        # Last 3 digits
        last3 = s[-3:]
        # Remaining digits
        remaining = s[:-3]
        # Group by 2
        groups = []
        while remaining:
            groups.append(remaining[-2:])
            remaining = remaining[:-2]
        
        groups.reverse()
        return ",".join(groups) + "," + last3

    return f"₹{format_indian(value)}"


@app.template_filter('percentage')
def percentage_filter(value):
    """Format as percentage"""
    if value is None:
        return '0.00%'
    return f"{value:.2f}%"


@app.template_filter('truncate_text')
def truncate_text(text, length=50):
    """Truncate text to specified length"""
    if len(text) <= length:
        return text
    return text[:length] + '...'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
