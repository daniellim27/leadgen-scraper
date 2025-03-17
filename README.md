# Private Equity Lead Generator

A web application for private equity firms to discover and analyze potential business leads using Google Maps data and AI-powered insights.

## Features

- **Business Search**: Find businesses by simply entering their website URL - location is automatically detected
- **Data Collection**: Automatically gather business details including:
  - Business name
  - Email address
  - Phone number
  - Website
  - CEO/Owner name
  - Location (automatically determined from URL)
- **AI Insights**: Get AI-powered analysis of business potential for investment
- **Data Export**: Export lead data to CSV or Excel formats

## Tech Stack

- Flask web framework
- Google Maps API for business data and location detection
- OpenAI API for business insights
- Bootstrap for responsive UI

## Setup Instructions

1. Clone this repository
2. Create a `.env` file in the root directory with the following variables:
   ```
   GOOGLE_MAPS_API_KEY=your_google_maps_api_key
   OPENAI_API_KEY=your_openai_api_key
   FLASK_SECRET_KEY=your_secret_key
   ```
3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Run the application:
   ```
   python app.py
   ```
5. Navigate to `http://localhost:5000` in your web browser

## Usage

1. Enter a business website URL - the system will automatically detect its location
2. Review the results in the interactive table
3. Select businesses to analyze with AI
4. Export selected leads to CSV or Excel

## License

MIT
