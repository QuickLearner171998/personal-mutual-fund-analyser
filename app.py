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

from core.unified_processor import (
    process_mf_central_complete, 
    aggregate_holdings_for_display,
    match_sips_with_holdings
)
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
    """Portfolio dashboard with aggregated holdings"""
    try:
        portfolio = store.get_portfolio()
        if not portfolio:
            logger.info("No portfolio data found in dashboard")
            return render_template('dashboard.html', summary=None, holdings=[], has_broker_info=False)
        
        holdings = portfolio.get('holdings', [])
        logger.info(f"Dashboard: Processing {len(holdings)} holdings")
        
        # Aggregate holdings for display
        aggregated_holdings, aggregation_map = aggregate_holdings_for_display(holdings)
        logger.info(f"Dashboard: Aggregated to {len(aggregated_holdings)} holdings, merged {len(aggregation_map)} duplicates")
        
        # Sort by current value
        aggregated_holdings = sorted(aggregated_holdings, key=lambda x: x.get('current_value', 0), reverse=True)
        
        # Check if any holdings have broker info
        has_broker_info = any(h.get('broker') for h in holdings)
        logger.info(f"Dashboard: Broker info available: {has_broker_info}")
        
        return render_template(
            'dashboard.html', 
            summary=portfolio, 
            holdings=aggregated_holdings,
            has_broker_info=has_broker_info
        )
    except Exception as e:
        import traceback
        logger.error(f'Dashboard error: {str(e)}')
        logger.error(f'Dashboard error traceback: {traceback.format_exc()}')
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return render_template('dashboard.html', summary=None, holdings=[], has_broker_info=False)


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    """File upload page"""
    if request.method == 'POST':
        excel_file = request.files.get('excel_file')
        transaction_json = request.files.get('transaction_json')
        xirr_json = request.files.get('xirr_json')
        
        logger.info("Upload request received")
        logger.info(f"Files: excel={excel_file.filename if excel_file else 'None'}, "
                   f"transaction={transaction_json.filename if transaction_json else 'None'}, "
                   f"xirr={xirr_json.filename if xirr_json else 'None'}")
        
        if not all([excel_file, transaction_json, xirr_json]):
            logger.warning("Missing files in upload request")
            flash('Please upload all 3 required files', 'error')
            return redirect(url_for('upload'))
        
        try:
            # Save files
            import shutil
            excel_path = os.path.join(UPLOAD_DIR, excel_file.filename)
            transaction_path = os.path.join(UPLOAD_DIR, transaction_json.filename)
            xirr_path = os.path.join(UPLOAD_DIR, xirr_json.filename)
            
            logger.info(f"Saving files to {UPLOAD_DIR}")
            excel_file.save(excel_path)
            transaction_json.save(transaction_path)
            xirr_json.save(xirr_path)
            logger.info("Files saved successfully")
            
            # Process files
            logger.info("Starting data processing")
            portfolio_data = process_mf_central_complete(
                excel_path=excel_path,
                transaction_json_path=transaction_path,
                xirr_json_path=xirr_path
            )
            logger.info(f"Data processing completed: {portfolio_data.get('num_funds', 0)} funds, "
                       f"{portfolio_data.get('num_active_sips', 0)} active SIPs")
            
            # Save to database
            logger.info("Saving to database")
            store.save_complete_data(
                portfolio=portfolio_data,
                transactions=[],
                sips=portfolio_data.get('active_sips', []),
                broker_info=portfolio_data.get('broker_info', {}),
                aggregation_map={}
            )
            logger.info("Database save completed")
            
            # Index for vector search
            try:
                logger.info("Starting vector indexing")
                index_portfolio_data(portfolio_data)
                logger.info("Vector indexing completed")
            except Exception as e:
                logger.warning(f"Vector indexing failed: {e}")
                import traceback
                logger.warning(f"Vector indexing traceback: {traceback.format_exc()}")
            
            flash(f'Successfully processed {portfolio_data.get("num_funds", 0)} funds!', 'success')
            logger.info("Upload completed successfully, redirecting to dashboard")
            return redirect(url_for('dashboard'))
        
        except Exception as e:
            import traceback
            logger.error(f'Upload failed: {str(e)}')
            logger.error(f'Upload error traceback: {traceback.format_exc()}')
            flash(f'Upload failed: {str(e)}', 'error')
            return redirect(url_for('upload'))
    
    return render_template('upload.html')


@app.route('/sip-analytics')
def sip_analytics():
    """SIP analytics page with returns data"""
    try:
        logger.info("Loading SIP analytics")
        portfolio = store.get_portfolio()
        sips = store.get_sips()
        
        if not portfolio or not sips:
            logger.warning("No portfolio or SIP data found")
            return render_template('sip_analytics.html', analytics=None, active_sips=[], inactive_sips=[], upcoming={'upcoming_sips': [], 'count': 0, 'total_amount': 0})
        
        # Get holdings for matching
        holdings = portfolio.get('holdings', [])
        logger.info(f"SIP Analytics: Matching {len(sips)} SIPs with {len(holdings)} holdings")
        
        # Match SIPs with holdings to get returns data
        enriched_sips = match_sips_with_holdings(sips, holdings)
        logger.info(f"SIP Analytics: Enriched {len(enriched_sips)} SIPs with returns data")
        
        # Separate active and inactive SIPs (already marked in the data)
        active_sips = [s for s in enriched_sips if s.get('is_active', False)]
        inactive_sips = [s for s in enriched_sips if not s.get('is_active', False)]
        
        logger.info(f"SIP Analytics: {len(active_sips)} active, {len(inactive_sips)} inactive")
        
        # Calculate analytics
        monthly_outflow = sum(s.get('sip_amount', 0) for s in active_sips if s.get('frequency', '').lower() == 'monthly')
        total_sip_invested = sum(s.get('total_invested_sip', 0) for s in active_sips)
        total_sip_current = sum(s.get('current_value', 0) for s in active_sips)
        
        analytics = {
            'data': {
                'total_sips': len(enriched_sips),
                'active_sips': len(active_sips),
                'inactive_sips': len(inactive_sips),
                'monthly_outflow': monthly_outflow,
                'avg_sip_amount': monthly_outflow / len(active_sips) if active_sips else 0,
                'total_invested': total_sip_invested,
                'total_current_value': total_sip_current,
                'total_returns': total_sip_current - total_sip_invested
            }
        }
        
        # Calculate upcoming SIPs (next 30 days)
        from datetime import datetime, date, timedelta
        today = date.today()
        upcoming = []
        total_amount = 0
        
        for sip in active_sips:
            last_date = sip.get('last_installment_date')
            frequency = sip.get('frequency', 'Monthly')
            
            if last_date:
                try:
                    # Handle date object or string
                    if isinstance(last_date, str):
                        last_date_obj = datetime.strptime(last_date, '%Y-%m-%d').date()
                    elif isinstance(last_date, date):
                        last_date_obj = last_date
                    else:
                        continue
                    
                    # Calculate next date based on frequency
                    if frequency.lower() == 'monthly':
                        # Add roughly a month
                        next_month = last_date_obj.month + 1 if last_date_obj.month < 12 else 1
                        next_year = last_date_obj.year if last_date_obj.month < 12 else last_date_obj.year + 1
                        try:
                            next_date = date(next_year, next_month, last_date_obj.day)
                        except ValueError:
                            # Handle month-end dates (e.g., Jan 31 -> Feb 28)
                            next_date = date(next_year, next_month, 28)
                    elif frequency.lower() == 'quarterly':
                        next_date = last_date_obj + timedelta(days=90)
                    elif frequency.lower() == 'weekly':
                        next_date = last_date_obj + timedelta(days=7)
                    else:
                        next_date = last_date_obj + timedelta(days=30)
                    
                    days_until = (next_date - today).days
                    
                    if 0 <= days_until <= 30:
                        upcoming.append({
                            'scheme_name': sip.get('scheme_name', ''),
                            'sip_amount': sip.get('sip_amount', 0),
                            'date': next_date.strftime('%Y-%m-%d'),
                            'days_until': days_until,
                            'broker': sip.get('broker', '')
                        })
                        total_amount += sip.get('sip_amount', 0)
                except Exception as e:
                    logger.warning(f"Error calculating next SIP date for {sip.get('scheme_name', 'Unknown')}: {e}")
                    continue
        
        upcoming.sort(key=lambda x: x['days_until'])
        
        upcoming_data = {
            'upcoming_sips': upcoming,
            'count': len(upcoming),
            'total_amount': total_amount
        }
        
        # Sort by current value
        active_sips = sorted(active_sips, key=lambda x: x.get('current_value', 0), reverse=True)
        inactive_sips = sorted(inactive_sips, key=lambda x: x.get('scheme_name', ''))
        
        logger.info(f"SIP Analytics: Rendering with {len(active_sips)} active, {len(inactive_sips)} inactive SIPs")
        
        return render_template(
            'sip_analytics.html', 
            analytics=analytics, 
            active_sips=active_sips,
            inactive_sips=inactive_sips,
            upcoming=upcoming_data
        )
    
    except Exception as e:
        import traceback
        logger.error(f'SIP analytics error: {str(e)}')
        logger.error(f'SIP analytics error traceback: {traceback.format_exc()}')
        flash(f'Error loading SIP analytics: {str(e)}', 'error')
        return render_template('sip_analytics.html', analytics=None, active_sips=[], inactive_sips=[], upcoming={'upcoming_sips': [], 'count': 0, 'total_amount': 0})


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
