import requests
from bs4 import BeautifulSoup
import re
import logging
import json
import os
from flask import Flask, jsonify, render_template
import configparser


# Load credentials from the ini file
API_config = configparser.ConfigParser()
API_config.read('credentials.ini')

# Get the Google API key
GOOGLE_MAPS_API_KEY = API_config['google']['api_key']

app = Flask(__name__)



# Configuration dictionary
config = {
    "base_url": "https://www.komo.co.il/code/nadlan/apartments-for-rent.asp",
    "city_url": "https://www.komo.co.il/code/nadlan/quick-links.asp?nehes=1&subLuachNum=1",
    "property_classes": ['Private', 'Real_estate_agent'],
    "pagination_id": "paging",
    "price_class": "tdPrice",
    "details_class": "tdMoreDetails",
    "gallery_class": "tdGallery",
    "address_class": "LinkModaaTitle"
}

# Set up logging
logging.basicConfig(level=logging.INFO)

def get_city_list():
    response = requests.get(config['city_url'])
    soup = BeautifulSoup(response.text, 'html.parser')
    cities = []
    for city_div in soup.find_all('div', class_='listFloatItem'):
        city_link = city_div.find('a')
        if 'cityname' in city_link.attrs:
            city_name = city_link['cityname']
            cities.append(city_name)
    return cities

def format_city_names(city_names):
    formatted_cities = []
    for city in city_names:
        formatted_city = city.replace('- ', '').replace(' ', '+')
        formatted_cities.append(formatted_city)
    return formatted_cities

def generate_url(city_name, page=1):
    formatted_city_name = city_name.replace(' ', '+')
    return f"{config['base_url']}?nehes=1&cityName={formatted_city_name}&currPage={page}"

def get_total_pages(city_name):
    url = generate_url(city_name)
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    pagination = soup.find('span', id=config['pagination_id'])
    if pagination:
        page_links = pagination.find_all('a', class_='paging')
        total_pages = max(int(link.text) for link in page_links if link.text.isdigit())
    else:
        total_pages = 1
    return total_pages

def extract_property_details(ad):
    title = ad.find('span', class_=config['address_class']).text.strip()
    location_parts = title.split(",")
    city = location_parts[0].strip() if len(location_parts) > 0 else 'N/A'
    area = location_parts[1].strip() if len(location_parts) > 1 else 'N/A'
    street_and_number = location_parts[2].strip() if len(location_parts) > 2 else 'N/A'

    street_parts = re.split(r'\s+(\d+)$', street_and_number)
    street = street_parts[0].strip() if street_parts else 'N/A'
    number = street_parts[1].strip() if len(street_parts) > 1 else 'N/A'

    price_raw = ad.find('td', class_=config['price_class']).text.strip()
    price = re.sub(r'\D', '', price_raw)

    details = ad.find('td', class_=config['details_class']).text.strip()
    room_count = re.search(r'(\d+(\.\d+)?)\s+חדרים', details)
    square_meters = re.search(r'(\d+)\s+מ"ר', details)
    floor = re.search(r'קומה:(\d+)', details)

    return {
        'location': {
            'city': city,
            'area': area,
            'street': street,
            'number': number
        },
        'price': price,
        'room_count': room_count.group(1) if room_count else 'N/A',
        'square_meters': square_meters.group(1) if square_meters else 'N/A',
        'floor': floor.group(1) if floor else 'N/A',
        'image_url': ad.find('td', class_=config['gallery_class']).find('img')['src'],
        'full_address': title
    }

def scrape_properties(formatted_city_name, page_limit=None):
    properties = []
    try:
        total_pages = get_total_pages(formatted_city_name)
        for page in range(1, min(total_pages + 1, page_limit + 1) if page_limit else total_pages + 1):
            url = generate_url(formatted_city_name, page)
            response = requests.get(url)
            if response.status_code != 200:
                logging.error(f"Failed to retrieve data for {formatted_city_name} on page {page}")
                continue
            soup = BeautifulSoup(response.text, 'html.parser')
            for ad in soup.find_all('div', class_=config['property_classes']):
                properties.append(extract_property_details(ad))

        print(f"return {len(properties)} lines of apartments in {formatted_city_name}")

    except Exception as e:
        logging.error(f"An error occurred: {e}")
    return properties

def save_properties_to_file(properties, city_name):
    # Sanitize city name to avoid issues with special characters in file names
    sanitized_city_name = re.sub(r'[^\w\s-]', '', city_name).replace(" ", "_")
    file_path = f"data/{sanitized_city_name}.json"

    # Ensure the directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # Write properties to JSON file
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(properties, f, ensure_ascii=False, indent=4)
    logging.info(f"Saved {len(properties)} properties for {city_name} to {file_path}")

def get_properties_from_file(city_name):
    # Sanitize city name to avoid issues with special characters in file names
    sanitized_city_name = re.sub(r'[^\w\s-]', '', city_name).replace(" ", "_")
    file_path = f"data/{sanitized_city_name}.json"

    try:
        # Read properties from JSON file
        with open(file_path, 'r', encoding='utf-8') as f:
            properties = json.load(f)
        return properties
    except FileNotFoundError:
        logging.error(f"No saved data found for {city_name} in {file_path}.")
        return None
    except json.JSONDecodeError:
        logging.error(f"Error decoding JSON from {file_path}.")
        return None

@app.route('/api/properties/<city_name>', methods=['GET'])
def get_properties(city_name):
    properties = get_properties_from_file(city_name)
    return jsonify(properties)

@app.route('/')
def index():
    return render_template('index.html', google_api_key=GOOGLE_MAPS_API_KEY)

def main():
    # using the crawler to update the info

    city_list = get_city_list()
    formatted_city_list = format_city_names(city_list)

    for city_to_scrape in formatted_city_list:
        properties = scrape_properties(city_to_scrape)
        save_properties_to_file(properties, city_to_scrape)
        logging.info(f"Scraped properties for {city_to_scrape} completed.")


    tlv = get_properties_from_file(formatted_city_list[0])
    print(tlv)

if __name__ == '__main__':
    #main() # use if you want to update the scraped data
    app.run(debug=True)
