import os

from dotenv import load_dotenv
from app import create_app

# Force reload environment variables from .env file
load_dotenv(override=True)
# Create the application
# Explicitly set GitHub token and base URL in environment
os.environ['GITHUB_TOKEN'] = os.environ.get('GITHUB_TOKEN')
os.environ['OPENAI_BASE_URL'] = os.environ.get('OPENAI_BASE_URL', 'https://models.inference.ai.azure.com')


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
