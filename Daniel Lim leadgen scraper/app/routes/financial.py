import logging
from flask import Blueprint, request, jsonify, current_app
from app.utils.financial_api import (
    search_company_by_name,
    get_company_profile,
    get_financial_ratios, 
    get_income_statement,
    get_balance_sheet,
    get_financial_summary
)

# Create blueprint
financial_bp = Blueprint('financial', __name__, url_prefix='/financial')
logger = logging.getLogger(__name__)

@financial_bp.route('/search', methods=['GET', 'POST'])
def search_company():
    """
    Search for a company by name to get financial data
    """
    if request.method == 'POST':
        data = request.get_json() or {}
        company_name = data.get('company_name', '')
        
        if not company_name:
            company_name = request.form.get('company_name', '')
            
        logger.info(f"Financial search request received for company: '{company_name}'")
        
        if not company_name:
            logger.warning("Empty company name provided")
            return jsonify({'success': False, 'error': 'Please provide a company name'})
        
        try:
            # Search for the company
            companies = search_company_by_name(company_name)
            
            if isinstance(companies, dict) and "error" in companies:
                return jsonify({'success': False, 'error': companies["error"]})
                
            if not companies:
                logger.info(f"No companies found for '{company_name}'")
                return jsonify({'success': True, 'companies': []})
            
            logger.info(f"Found {len(companies)} companies matching '{company_name}'")
            return jsonify({'success': True, 'companies': companies})
            
        except Exception as e:
            logger.error(f"Error in company search: {str(e)}")
            return jsonify({'success': False, 'error': str(e)})
    
    # GET request - render search form
    return jsonify({'success': True, 'message': 'Use POST to search for companies'})

@financial_bp.route('/company/<ticker>', methods=['GET'])
def company_financial_data(ticker):
    """
    Get financial data for a company by ticker symbol
    """
    logger.info(f"Fetching financial data for ticker: {ticker}")
    
    try:
        # Get financial summary for the company
        data = get_financial_summary(ticker)
        
        if isinstance(data, dict) and "error" in data:
            return jsonify({'success': False, 'error': data["error"]})
        
        return jsonify({'success': True, 'data': data})
        
    except Exception as e:
        logger.error(f"Error fetching financial data for {ticker}: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@financial_bp.route('/profile/<ticker>', methods=['GET'])
def company_profile(ticker):
    """
    Get company profile by ticker symbol
    """
    logger.info(f"Fetching company profile for ticker: {ticker}")
    
    try:
        # Get company profile
        profile = get_company_profile(ticker)
        
        if isinstance(profile, dict) and "error" in profile:
            return jsonify({'success': False, 'error': profile["error"]})
        
        return jsonify({'success': True, 'profile': profile})
        
    except Exception as e:
        logger.error(f"Error fetching profile for {ticker}: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@financial_bp.route('/ratios/<ticker>', methods=['GET'])
def company_ratios(ticker):
    """
    Get financial ratios by ticker symbol
    """
    logger.info(f"Fetching financial ratios for ticker: {ticker}")
    
    try:
        # Get financial ratios
        ratios = get_financial_ratios(ticker)
        
        if isinstance(ratios, dict) and "error" in ratios:
            return jsonify({'success': False, 'error': ratios["error"]})
        
        return jsonify({'success': True, 'ratios': ratios})
        
    except Exception as e:
        logger.error(f"Error fetching ratios for {ticker}: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@financial_bp.route('/income/<ticker>', methods=['GET'])
def company_income(ticker):
    """
    Get income statement by ticker symbol
    """
    period = request.args.get('period', 'annual')
    limit = int(request.args.get('limit', 1))
    
    logger.info(f"Fetching {period} income statement for ticker: {ticker}")
    
    try:
        # Get income statement
        income = get_income_statement(ticker, period, limit)
        
        if isinstance(income, dict) and "error" in income:
            return jsonify({'success': False, 'error': income["error"]})
        
        return jsonify({'success': True, 'income_statement': income})
        
    except Exception as e:
        logger.error(f"Error fetching income statement for {ticker}: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@financial_bp.route('/balance/<ticker>', methods=['GET'])
def company_balance(ticker):
    """
    Get balance sheet by ticker symbol
    """
    period = request.args.get('period', 'annual')
    limit = int(request.args.get('limit', 1))
    
    logger.info(f"Fetching {period} balance sheet for ticker: {ticker}")
    
    try:
        # Get balance sheet
        balance = get_balance_sheet(ticker, period, limit)
        
        if isinstance(balance, dict) and "error" in balance:
            return jsonify({'success': False, 'error': balance["error"]})
        
        return jsonify({'success': True, 'balance_sheet': balance})
        
    except Exception as e:
        logger.error(f"Error fetching balance sheet for {ticker}: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}) 