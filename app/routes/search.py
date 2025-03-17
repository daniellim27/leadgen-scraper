import os
import json
import pandas as pd
import traceback
from flask import Blueprint, render_template, request, jsonify, send_file, current_app
from app.utils.maps_api import search_businesses, get_business_details
from app.utils.financial_api import search_company_by_name, get_financial_summary
from app.utils.openai_insights import generate_business_insights
from werkzeug.utils import secure_filename
import tempfile

search_bp = Blueprint('search', __name__, url_prefix='/search')

@search_bp.route('/', methods=['GET', 'POST'])
def search():
    """Handle the search page and form submission."""
    if request.method == 'POST':
        query = request.form.get('query', '').strip()
        
        current_app.logger.info(f"Search request received: query='{query}'")
        
        # Validate inputs
        if not query:
            current_app.logger.warning("Empty query provided")
            return jsonify({'success': False, 'error': 'Please enter a business URL'})
        
        try:
            # Search for businesses based on query only - location will be determined from URL
            current_app.logger.info(f"Calling search_businesses with query='{query}'")
            businesses = search_businesses(query)
            
            # Log the result summary
            if businesses:
                current_app.logger.info(f"Search successful: Found {len(businesses)} businesses")
                business_names = [b.get('name') for b in businesses]
                current_app.logger.info(f"Found businesses: {', '.join(business_names)}")
            else:
                current_app.logger.warning(f"No businesses found for query='{query}'")
                
            if not businesses:
                current_app.logger.info("No businesses found for the search criteria")
                return jsonify({'success': True, 'businesses': []})
                
            return jsonify({'success': True, 'businesses': businesses})
        except ValueError as e:
            # Handle specific validation errors from our code
            error_message = str(e)
            current_app.logger.error(f"Validation error in search: {error_message}")
            return jsonify({'success': False, 'error': error_message})
        except Exception as e:
            error_trace = traceback.format_exc()
            current_app.logger.error(f"Error searching businesses: {str(e)}\n{error_trace}")
            return jsonify({'success': False, 'error': f"An error occurred while searching: {str(e)}"})
    
    return render_template('search.html')

@search_bp.route('/business/<place_id>', methods=['GET'])
def business_details(place_id):
    """Get detailed information about a specific business."""
    current_app.logger.info(f"Business details requested for place_id: {place_id}")
    
    try:
        details = get_business_details(place_id)
        
        # Try to fetch financial data if we have a business name
        financial_data = None
        if details and 'name' in details:
            business_name = details['name']
            current_app.logger.info(f"Searching for financial data for: {business_name}")
            
            # Search for company by name
            companies = search_company_by_name(business_name)
            
            # If we found any matching companies
            if companies and not isinstance(companies, dict):
                if len(companies) > 0:
                    # Get the first match
                    first_company = companies[0]
                    ticker = first_company.get('symbol')
                    
                    if ticker:
                        current_app.logger.info(f"Found ticker {ticker} for {business_name}, fetching financial data")
                        financial_data = get_financial_summary(ticker)
                        
                        # Add ticker and company name for reference
                        financial_data['ticker'] = ticker
                        financial_data['company_name'] = first_company.get('name', business_name)
                    else:
                        current_app.logger.warning(f"No ticker found for {business_name}")
                else:
                    current_app.logger.warning(f"No companies found matching {business_name}")
        
        return jsonify({
            'success': True, 
            'details': details,
            'financial_data': financial_data
        })
        
    except Exception as e:
        error_trace = traceback.format_exc()
        current_app.logger.error(f"Error fetching business details: {str(e)}\n{error_trace}")
        return jsonify({'success': False, 'error': str(e)})

@search_bp.route('/analyze', methods=['POST'])
def analyze_business():
    """Generate AI insights for a business."""
    data = request.json
    business_data = data.get('business_data', {})
    
    try:
        insights = generate_business_insights(business_data)
        return jsonify({'success': True, 'insights': insights})
    except Exception as e:
        current_app.logger.error(f"Error generating insights: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@search_bp.route('/export', methods=['POST'])
def export_data():
    """Export selected business data to CSV or Excel."""
    # Check if the request is JSON or form data
    if request.is_json:
        data = request.get_json()
        export_format = data.get('format', 'csv')
        businesses = data.get('businesses', [])
        current_app.logger.info(f"Export JSON request received: format={export_format}, businesses count={len(businesses)}")
    else:
        export_format = request.form.get('format', 'csv')
        businesses_json = request.form.get('businesses', '[]')
        current_app.logger.info(f"Export form request received: format={export_format}, data length={len(businesses_json)}")
        try:
            businesses = json.loads(businesses_json)
        except json.JSONDecodeError as json_error:
            error_msg = f"Invalid JSON data provided: {str(json_error)}"
            current_app.logger.error(error_msg)
            current_app.logger.error(f"Received JSON: {businesses_json[:100]}...")  # Log first 100 chars
            return jsonify({'success': False, 'error': error_msg})
    
    try:
        if not businesses:
            current_app.logger.warning("No businesses selected for export")
            return jsonify({'success': False, 'error': 'No businesses selected for export'})
        
        current_app.logger.info(f"Exporting {len(businesses)} businesses")
        
        # Create a DataFrame from the business data
        df = pd.DataFrame(businesses)
        
        # Create a temporary file for the export
        temp_dir = tempfile.gettempdir()
        if export_format == 'excel':
            temp_filename = os.path.join(temp_dir, "business_leads_export.xlsx")
        else:
            export_format = 'csv'  # Ensure format is set correctly
            temp_filename = os.path.join(temp_dir, "business_leads_export.csv")
        current_app.logger.info(f"Temp filename: {temp_filename}")
            
        if export_format == 'csv':
            df.to_csv(temp_filename, index=False, encoding='utf-8-sig')  # Use utf-8-sig to handle special characters
            mimetype = 'text/csv'
            download_name = 'business_leads.csv'
        else:  # excel
            # Ensure openpyxl is available for Excel export
            try:
                current_app.logger.info("Attempting to create Excel file")
                df.to_excel(temp_filename, index=False, engine='openpyxl')
                mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                download_name = 'business_leads.xlsx'
            except Exception as excel_error:
                current_app.logger.error(f"Excel export error: {str(excel_error)}")
                # Fallback to CSV if Excel export fails
                export_format = 'csv'
                temp_filename = os.path.join(temp_dir, "business_leads_export.csv")
                current_app.logger.info(f"Falling back to CSV: {temp_filename}")
                df.to_csv(temp_filename, index=False, encoding='utf-8-sig')
                mimetype = 'text/csv'
                download_name = 'business_leads.csv'
        
        # Ensure the file exists before attempting to send it
        if not os.path.exists(temp_filename):
            error_msg = f"Generated file {temp_filename} not found"
            current_app.logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        file_size = os.path.getsize(temp_filename)
        current_app.logger.info(f"File created successfully, size: {file_size} bytes")
        
        # Check if file is empty
        if file_size == 0:
            error_msg = "Generated file is empty"
            current_app.logger.error(error_msg)
            return jsonify({'success': False, 'error': error_msg})
            
        return send_file(
            temp_filename,
            mimetype=mimetype,
            as_attachment=True,
            download_name=download_name
        )
    
    except Exception as e:
        error_msg = f"Error exporting data: {str(e)}"
        current_app.logger.error(error_msg)
        current_app.logger.error(traceback.format_exc())  # Log the full traceback
        return jsonify({'success': False, 'error': error_msg}) 