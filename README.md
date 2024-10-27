
# Real Estate Property Map

This project displays real estate properties on Google Maps using a Flask backend to scrape property data and serve it to a frontend that visualizes the locations on a map.

## Table of Contents
- [Requirements](#requirements)
- [Setup](#setup)
- [Usage](#usage)
- [Updating Credentials](#updating-credentials)
- [File Structure](#file-structure)
- [License](#license)

## Requirements

- Python 3.x
- Flask
- Requests
- Google Maps API

## Setup

1. **Install the required packages:

   Then install the packages:

   ```bash
   pip install -r requirements.txt
   ```

5. **Edit the a `credentials.ini` file in the project directory to store your Google Maps API key.

   **Make sure to update `YOUR_GOOGLE_MAPS_API_KEY` with your actual Google Maps API key.** You can obtain an API key from the [Google Cloud Console](https://console.cloud.google.com/).

## Usage

1. **run the web_scraper application:**

2. **Open your browser and navigate to** `http://127.0.0.1:5000` **to view the application.**

3. The application will fetch properties data for the specified city and display them on the map.

## File Structure

```plaintext
.
├── .venv/                   # Virtual environment directory
├── web_scrape.py            # Python script for web scraping and Flask backend
├── index.html               # Frontend HTML file for displaying the map
├── requirements.txt         # Python dependencies
├── credentials.ini          # File for storing API credentials
└── README.md                # Project documentation
```

## License

This project is licensed under the MIT License. See the LICENSE file for more details.
