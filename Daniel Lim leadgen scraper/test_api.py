import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Get GitHub token and endpoint
github_token = os.getenv('GITHUB_TOKEN')
github_endpoint = os.getenv('OPENAI_BASE_URL', 'https://models.inference.ai.azure.com')
model_name = 'gpt-4o'

# Check token
if not github_token:
    print("ERROR: GitHub token not found in environment variables")
    exit(1)

# Mask token for security
masked_token = github_token[:10] + "..." if github_token else "None"
print(f"GitHub Token: {masked_token}")
print(f"Using endpoint: {github_endpoint}")

try:
    # Initialize OpenAI client with GitHub configuration
    client = OpenAI(
        base_url=github_endpoint,
        api_key=github_token,
    )
    
    # Make a simple API call
    response = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": "Say hello"}],
        max_tokens=10
    )
    
    print("API call successful!")
    print(f"Response: {response}")
    
except Exception as e:
    print(f"Error: {str(e)}") 