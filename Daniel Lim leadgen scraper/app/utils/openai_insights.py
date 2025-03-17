import os
import logging
import json
import re
from openai import OpenAI

# Initialize logger
logger = logging.getLogger(__name__)

def get_api_key_type(api_key):
    """
    Determine the type of OpenAI API key.
    
    Args:
        api_key (str): The OpenAI API key
        
    Returns:
        str: The type of API key (legacy, project, or service account)
    """
    if not api_key:
        return "undefined"
    elif api_key.startswith("sk-proj-"):
        return "project key (new format)"
    elif api_key.startswith("sk-svcacct-"):
        return "service account (new format)"
    elif api_key.startswith("sk-"):
        return "legacy key (deprecated)"
    else:
        return "unknown format"

def generate_business_insights(business_data):
    """
    Generate private equity investment insights based on business data.
    
    Args:
        business_data (dict): Business information
        
    Returns:
        dict: Investment insights
    """
    # Get the GitHub token and endpoint at function call time
    github_token = os.environ.get('GITHUB_TOKEN')
    github_endpoint = os.environ.get('OPENAI_BASE_URL', 'https://models.inference.ai.azure.com')
    model_name = 'gpt-4o'
    
    if not github_token:
        raise ValueError("GitHub token is not configured")
    
    # Initialize the client with the GitHub credentials
    client = OpenAI(
        base_url=github_endpoint,
        api_key=github_token,
    )
    
    # Extract business information
    business_name = business_data.get('name', '')
    business_website = business_data.get('website', '')
    business_address = business_data.get('address', '')
    business_rating = business_data.get('rating', '')
    
    # Create a prompt for OpenAI
    prompt = f"""
    You are a private equity analyst tasked with providing an initial assessment of a potential investment target.
    Based on the available information, provide a brief analysis of this business from a private equity perspective:
    
    Business Name: {business_name}
    Website: {business_website}
    Address: {business_address}
    Rating: {business_rating if business_rating else 'Not available'}
    
    Please include the following in your analysis:
    1. Potential for growth and scalability
    2. Market position assessment
    3. Possible value creation strategies
    4. Initial risk factors
    5. Recommended next steps for due diligence
    
    Format your response as JSON with the following structure:
    {{
        "summary": "Brief 2-3 sentence summary of investment potential",
        "growth_potential": "Assessment of growth potential",
        "market_position": "Assessment of market position",
        "value_creation": "Potential value creation strategies",
        "risk_factors": "Key risk factors to consider",
        "next_steps": "Recommended next steps for further analysis"
    }}
    """
    
    try:
        # Log that we're using GitHub-based AI model
        logger.info(f"Using GitHub AI with endpoint: {github_endpoint}")
        
        # Call API for insights
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a private equity analyst providing investment insights in JSON format only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=800
        )
        
        # Extract and parse the JSON response
        content = response.choices[0].message.content
        
        # Try to extract JSON from the response
        try:
            # If the response is already valid JSON
            insights = json.loads(content)
        except json.JSONDecodeError:
            # If the response contains text before/after JSON
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = content[json_start:json_end]
                insights = json.loads(json_str)
            else:
                # Fallback structure if JSON parsing fails
                insights = {
                    "summary": "Unable to generate structured insights.",
                    "growth_potential": "Analysis not available.",
                    "market_position": "Analysis not available.",
                    "value_creation": "Analysis not available.",
                    "risk_factors": "Analysis not available.",
                    "next_steps": "Analysis not available."
                }
        
        return insights
        
    except Exception as e:
        logger.error(f"Error generating insights with GitHub AI: {str(e)}")
        return {
            "summary": f"Error generating insights: {str(e)}",
            "growth_potential": "Analysis not available.",
            "market_position": "Analysis not available.",
            "value_creation": "Analysis not available.",
            "risk_factors": "Analysis not available.",
            "next_steps": "Analysis not available."
        } 