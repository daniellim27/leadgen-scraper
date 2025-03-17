import os
import requests
import logging
from dotenv import load_dotenv

# Set up logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get API key from environment variables (we'll need to add this to .env)
FMP_API_KEY = os.environ.get('FMP_API_KEY')
BASE_URL = "https://financialmodelingprep.com/api/v3"

def search_company_by_name(name):
    """
    Search for a company by name to get its ticker symbol
    
    Args:
        name (str): The company name to search for
        
    Returns:
        list: List of matching companies with their details
    """
    logger.info(f"Searching for company with name: {name}")
    
    if not FMP_API_KEY:
        logger.error("FMP_API_KEY is missing from environment variables")
        return {"error": "API key not configured"}
    
    try:
        endpoint = f"{BASE_URL}/search?query={name}&limit=10&apikey={FMP_API_KEY}"
        response = requests.get(endpoint)
        response.raise_for_status()
        
        companies = response.json()
        logger.info(f"Found {len(companies)} companies matching '{name}'")
        return companies
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error searching for company '{name}': {str(e)}")
        return {"error": str(e)}

def get_company_profile(ticker):
    """
    Get detailed profile information for a company by ticker symbol
    
    Args:
        ticker (str): The stock ticker symbol
        
    Returns:
        dict: Company profile data
    """
    logger.info(f"Getting profile for company with ticker: {ticker}")
    
    if not FMP_API_KEY:
        logger.error("FMP_API_KEY is missing from environment variables")
        return {"error": "API key not configured"}
    
    try:
        endpoint = f"{BASE_URL}/profile/{ticker}?apikey={FMP_API_KEY}"
        response = requests.get(endpoint)
        response.raise_for_status()
        
        profiles = response.json()
        if not profiles:
            logger.warning(f"No profile found for ticker '{ticker}'")
            return {"error": "Company not found"}
        
        return profiles[0]  # Return the first profile
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error getting profile for ticker '{ticker}': {str(e)}")
        return {"error": str(e)}

def get_financial_ratios(ticker):
    """
    Get key financial ratios for a company
    
    Args:
        ticker (str): The stock ticker symbol
        
    Returns:
        dict: Financial ratios data
    """
    logger.info(f"Getting financial ratios for company with ticker: {ticker}")
    
    if not FMP_API_KEY:
        logger.error("FMP_API_KEY is missing from environment variables")
        return {"error": "API key not configured"}
    
    try:
        endpoint = f"{BASE_URL}/ratios-ttm/{ticker}?apikey={FMP_API_KEY}"
        response = requests.get(endpoint)
        response.raise_for_status()
        
        ratios = response.json()
        if not ratios:
            logger.warning(f"No financial ratios found for ticker '{ticker}'")
            return {"error": "Financial ratios not found"}
        
        return ratios[0]  # Return the first set of ratios
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error getting financial ratios for ticker '{ticker}': {str(e)}")
        return {"error": str(e)}

def get_income_statement(ticker, period="annual", limit=1):
    """
    Get income statement for a company
    
    Args:
        ticker (str): The stock ticker symbol
        period (str): 'annual' or 'quarter'
        limit (int): Number of periods to retrieve
        
    Returns:
        list: Income statement data
    """
    logger.info(f"Getting {period} income statement for company with ticker: {ticker}")
    
    if not FMP_API_KEY:
        logger.error("FMP_API_KEY is missing from environment variables")
        return {"error": "API key not configured"}
    
    try:
        endpoint = f"{BASE_URL}/income-statement/{ticker}?period={period}&limit={limit}&apikey={FMP_API_KEY}"
        response = requests.get(endpoint)
        response.raise_for_status()
        
        statements = response.json()
        if not statements:
            logger.warning(f"No income statement found for ticker '{ticker}'")
            return {"error": "Income statement not found"}
        
        return statements
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error getting income statement for ticker '{ticker}': {str(e)}")
        return {"error": str(e)}

def get_balance_sheet(ticker, period="annual", limit=1):
    """
    Get balance sheet for a company
    
    Args:
        ticker (str): The stock ticker symbol
        period (str): 'annual' or 'quarter'
        limit (int): Number of periods to retrieve
        
    Returns:
        list: Balance sheet data
    """
    logger.info(f"Getting {period} balance sheet for company with ticker: {ticker}")
    
    if not FMP_API_KEY:
        logger.error("FMP_API_KEY is missing from environment variables")
        return {"error": "API key not configured"}
    
    try:
        endpoint = f"{BASE_URL}/balance-sheet-statement/{ticker}?period={period}&limit={limit}&apikey={FMP_API_KEY}"
        response = requests.get(endpoint)
        response.raise_for_status()
        
        statements = response.json()
        if not statements:
            logger.warning(f"No balance sheet found for ticker '{ticker}'")
            return {"error": "Balance sheet not found"}
        
        return statements
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error getting balance sheet for ticker '{ticker}': {str(e)}")
        return {"error": str(e)}

def get_financial_summary(ticker):
    """
    Get a comprehensive financial summary for a company
    
    Args:
        ticker (str): The stock ticker symbol
        
    Returns:
        dict: Combined financial data
    """
    logger.info(f"Getting financial summary for company with ticker: {ticker}")
    
    # Get company profile
    profile = get_company_profile(ticker)
    if "error" in profile:
        return profile
    
    # Get financial ratios
    ratios = get_financial_ratios(ticker)
    
    # Get latest income statement
    income = get_income_statement(ticker)
    if isinstance(income, list) and income:
        income = income[0]
    
    # Get latest balance sheet
    balance = get_balance_sheet(ticker)
    if isinstance(balance, list) and balance:
        balance = balance[0]
    
    # Combine all data into a comprehensive summary
    summary = {
        "profile": profile,
        "financial_ratios": ratios,
        "income_statement": income,
        "balance_sheet": balance
    }
    
    return summary 