import os
import re
import json
import requests
import logging
from bs4 import BeautifulSoup
from urllib.parse import urlparse, quote_plus

# Get API key from environment variables
GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY')

logger = logging.getLogger(__name__)

# Places API v1 endpoint base URL
PLACES_API_BASE_URL = "https://places.googleapis.com/v1"

def extract_domain(url):
    """
    Extract the domain name from a URL.
    
    Args:
        url (str): Full URL of a business website
        
    Returns:
        str: Domain name without protocol and www
    """
    try:
        logger.info(f"Extracting domain from URL: {url}")
        
        # Handle empty strings or None values
        if not url:
            logger.warning("Empty URL provided to extract_domain")
            return ""
            
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            logger.info(f"Added https:// prefix, URL is now: {url}")
        
        # Parse the URL
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        
        # Handle case where parsing fails and netloc is empty
        if not domain:
            logger.warning(f"Failed to extract domain from {url}, using as is")
            # Strip any http/https if present and just use the input as domain
            cleaned_url = url.replace('https://', '').replace('http://', '')
            return cleaned_url.split('/')[0]  # Get the first part before any slashes
        
        # Remove www. if present
        if domain.startswith('www.'):
            domain = domain[4:]
            
        logger.info(f"Successfully extracted domain: {domain}")
        return domain
    except Exception as e:
        logger.error(f"Error extracting domain from URL: {str(e)}")
        # In case of error, return a sanitized version of the original input
        cleaned_url = url.replace('https://', '').replace('http://', '')
        return cleaned_url.split('/')[0] if '/' in cleaned_url else cleaned_url

def search_businesses(query, location=None, max_results=20):
    """
    Search for businesses based on query and location using Places API v1.
    
    Args:
        query (str): Type of business to search for, or a website URL
        location (str, optional): Location to search in. If not provided, will attempt to determine from URL.
        max_results (int): Maximum number of results to return
        
    Returns:
        list: List of business data dictionaries
    """
    try:
        if not GOOGLE_MAPS_API_KEY:
            raise ValueError("Google Maps API key is not configured")
        
        logger.info(f"Searching for businesses with query='{query}', initial location='{location}'")
        
        # Handle empty queries
        if not query or not query.strip():
            logger.error("Empty query provided")
            raise ValueError("Search query cannot be empty")
                
        # Check if query is a URL, and if so, extract the domain name and convert to business name
        search_query = query
        is_domain_search = False
        domain = None
        if query.startswith(('http://', 'https://')) or '.' in query:
            try:
                domain = extract_domain(query)
                if domain:
                    # Extract company name from domain (remove TLD)
                    company_name = domain.split('.')[0]
                    # Convert common abbreviations like "walmart" to proper name
                    search_query = company_name
                    is_domain_search = True
                    logger.info(f"Extracted company name from domain: '{search_query}'")
                    
                    # For major retailers/websites, try direct name search
                    if search_query.lower() in ['walmart', 'target', 'amazon', 'costco', 'bestbuy']:
                        search_query = search_query.lower()
                        if search_query == 'walmart':
                            search_query = 'Walmart'
                        elif search_query == 'target':
                            search_query = 'Target'
                        elif search_query == 'amazon':
                            search_query = 'Amazon'
                        elif search_query == 'costco':
                            search_query = 'Costco'
                        elif search_query == 'bestbuy':
                            search_query = 'Best Buy'
                        logger.info(f"Recognized major retailer, using name: '{search_query}'")
                else:
                    logger.warning(f"Could not extract domain from '{query}', using as is")
            except Exception as e:
                logger.error(f"Error processing URL query: {str(e)}")
                search_query = query  # Fallback to using original query
        
        businesses = []
        
        # If location is not provided, use a default
        if not location or not location.strip():
            location = "United States"  # Default fallback
            logger.warning("Using default location: 'United States'")
        
        # Prepare search text - for domains, just use the company name without location
        # to improve chances of finding a match for large businesses
        if is_domain_search:
            # For domain-based searches, try both with and without location
            search_text = search_query
            logger.info(f"Searching for domain-based business with query: '{search_text}'")
        else:
            search_text = f"{search_query} in {location}" if location else search_query
            logger.info(f"Final search query: '{search_text}'")
        
        # Prepare the request to Places API v1 text search endpoint
        url = f"{PLACES_API_BASE_URL}/places:searchText"
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": GOOGLE_MAPS_API_KEY,
            "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.id,places.rating,places.userRatingCount,places.location",
            "Referer": "http://localhost:5000"  # Add a referer header to match API key restrictions
        }
        
        # Create request payload
        payload = {
            "textQuery": search_text,
            "languageCode": "en",
            "maxResultCount": max_results
        }
        
        # Make the API request
        logger.info(f"Making API request to {url} with payload: {payload}")
        response = requests.post(url, headers=headers, json=payload)
        
        # Log response status and first part of content for debugging
        logger.info(f"API response status: {response.status_code}")
        logger.info(f"API response preview: {response.text[:200]}..." if len(response.text) > 200 else f"API response: {response.text}")
        
        response.raise_for_status()  # Raise exception for HTTP errors
        
        places_result = response.json()
        
        # Extract and process results
        places = places_result.get('places', [])
        total_results = len(places)
        logger.info(f"Found {total_results} business results from Google Maps API v1")
        
        for place in places:
            business = {
                'place_id': place.get('id'),
                'name': place.get('displayName', {}).get('text', ''),
                'address': place.get('formattedAddress', ''),
                'rating': place.get('rating', 'N/A'),
                'total_ratings': place.get('userRatingCount', 0),
                'location': {
                    'lat': place.get('location', {}).get('latitude'),
                    'lng': place.get('location', {}).get('longitude')
                }
            }
            businesses.append(business)
            
        # If no results found when searching by domain, try multiple alternative approaches
        if not businesses:
            logger.info(f"No results found for primary search '{search_text}', trying alternative searches")
            
            # Try a variety of alternative search approaches
            alt_search_queries = []
            
            if is_domain_search:
                # For domain searches, try with business suffix and without location
                alt_search_queries.append(f"{search_query} business")
                alt_search_queries.append(f"{search_query} store")
                alt_search_queries.append(f"{search_query} company")
                
                # For walmart.com and other major retailers, try direct search
                if search_query.lower() in ['walmart', 'target', 'amazon', 'costco', 'bestbuy']:
                    alt_search_queries.append(search_query)  # Just the name
            else:
                # For non-domain searches, try variations
                alt_search_queries.append(search_query)
                if location and location.strip():
                    alt_search_queries.append(f"{search_query} {location}")
            
            # Try each alternative search until we find results
            for alt_query in alt_search_queries:
                logger.info(f"Trying alternative search query: '{alt_query}'")
                
                alt_payload = {
                    "textQuery": alt_query,
                    "languageCode": "en",
                    "maxResultCount": max_results
                }
                
                try:
                    alt_response = requests.post(url, headers=headers, json=alt_payload)
                    alt_response.raise_for_status()
                    alt_result = alt_response.json()
                    
                    alt_places = alt_result.get('places', [])
                    logger.info(f"Found {len(alt_places)} business results from alternative search: '{alt_query}'")
                    
                    if alt_places:
                        for place in alt_places:
                            business = {
                                'place_id': place.get('id'),
                                'name': place.get('displayName', {}).get('text', ''),
                                'address': place.get('formattedAddress', ''),
                                'rating': place.get('rating', 'N/A'),
                                'total_ratings': place.get('userRatingCount', 0),
                                'location': {
                                    'lat': place.get('location', {}).get('latitude'),
                                    'lng': place.get('location', {}).get('longitude')
                                }
                            }
                            businesses.append(business)
                        
                        # If we found results, stop trying alternative queries
                        if businesses:
                            break
                except Exception as e:
                    logger.error(f"Error in alternative search '{alt_query}': {str(e)}")
                    continue
        
        return businesses
        
    except requests.exceptions.RequestException as e:
        logger.error(f"API request error in search_businesses: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Response status: {e.response.status_code}, Content: {e.response.text[:500]}")
        raise
    except Exception as e:
        logger.error(f"Error in search_businesses: {str(e)}")
        raise

def get_business_details(place_id):
    """
    Get detailed information about a specific business using Places API v1.
    
    Args:
        place_id (str): Google Maps Place ID
        
    Returns:
        dict: Detailed business information
    """
    if not GOOGLE_MAPS_API_KEY:
        raise ValueError("Google Maps API key is not configured")
    
    try:
        logger.info(f"Getting details for place_id: {place_id}")
        
        # Using Places API v1 for getting place details
        url = f"{PLACES_API_BASE_URL}/places/{place_id}"
        headers = {
            "X-Goog-Api-Key": GOOGLE_MAPS_API_KEY,
            "X-Goog-FieldMask": "id,displayName,formattedAddress,internationalPhoneNumber,websiteUri,rating,userRatingCount,googleMapsUri,types,location",
            "Referer": "http://localhost:5000"  # Add a referer header to match API key restrictions
        }
        
        # Make the API request
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        details = response.json()
        
        business_details = {
            'place_id': details.get('id'),
            'name': details.get('displayName', {}).get('text', ''),
            'address': details.get('formattedAddress', ''),
            'phone': details.get('internationalPhoneNumber', ''),
            'website': details.get('websiteUri', ''),
            'types': details.get('types', []),
            'rating': details.get('rating', 'N/A'),
            'total_ratings': details.get('userRatingCount', 0),
            'maps_url': details.get('googleMapsUri', '')
        }
        
        # Try to find the email and CEO info from the website
        if business_details['website']:
            try:
                email, ceo_name = extract_email_and_ceo(business_details['website'])
                business_details['email'] = email
                business_details['ceo_name'] = ceo_name
            except Exception as e:
                logger.error(f"Error extracting email/CEO info: {str(e)}")
                business_details['email'] = ''
                business_details['ceo_name'] = ''
        else:
            business_details['email'] = ''
            business_details['ceo_name'] = ''
        
        return business_details
        
    except Exception as e:
        logger.error(f"Error getting business details: {str(e)}")
        raise

def extract_email_and_ceo(website_url):
    """
    Extract email address and CEO name from a business website.
    
    Args:
        website_url (str): URL of the business website
        
    Returns:
        tuple: (email, ceo_name)
    """
    email = ""
    ceo_name = ""
    
    try:
        # Make a request to the website
        response = requests.get(website_url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract all text from the page
        page_text = soup.get_text()
        
        # Look for email patterns
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(email_pattern, page_text)
        if emails:
            # Filter out common noreply emails
            valid_emails = [e for e in emails if 'noreply' not in e and 'no-reply' not in e]
            if valid_emails:
                email = valid_emails[0]
        
        # Look for common CEO patterns in the text
        ceo_patterns = [
            r'CEO[:\s]*([\w\s\.]+)',
            r'Chief Executive Officer[:\s]*([\w\s\.]+)',
            r'Founder[:\s]*([\w\s\.]+)',
            r'President[:\s]*([\w\s\.]+)',
            r'Owner[:\s]*([\w\s\.]+)'
        ]
        
        for pattern in ceo_patterns:
            matches = re.search(pattern, page_text)
            if matches:
                ceo_name = matches.group(1).strip()
                break
        
        # If not found in patterns, try to look in about/team pages
        if not ceo_name:
            # Find links that might contain CEO info
            about_links = []
            for a in soup.find_all('a', href=True):
                href = a['href']
                link_text = a.get_text().lower()
                if ('about' in link_text or 'team' in link_text or 'leadership' in link_text) or \
                   ('about' in href or 'team' in href or 'leadership' in href):
                    # Ensure it's a full URL
                    if not href.startswith('http'):
                        if href.startswith('/'):
                            href = website_url.rstrip('/') + href
                        else:
                            href = website_url.rstrip('/') + '/' + href
                    about_links.append(href)
            
            # Visit the first valid about link
            for about_url in about_links[:2]:  # Limit to first 2 to avoid too many requests
                try:
                    about_response = requests.get(about_url, timeout=10)
                    about_soup = BeautifulSoup(about_response.text, 'html.parser')
                    about_text = about_soup.get_text()
                    
                    for pattern in ceo_patterns:
                        matches = re.search(pattern, about_text)
                        if matches:
                            ceo_name = matches.group(1).strip()
                            break
                    
                    if ceo_name:
                        break
                        
                except Exception:
                    continue
    
    except Exception as e:
        logger.error(f"Error extracting data from website: {str(e)}")
    
    return email, ceo_name 