import os
import json
from datetime import datetime
from urllib.request import Request, urlopen
import boto3

# Environment variables
API_KEY = os.environ['api_key']  # API key for the sailing data API
SAILING_SITE = os.environ['sailing_site']  # Sailing data API endpoint
BUCKET_NAME = os.environ['bucket_name']  # S3 bucket name
WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"

s3_client = boto3.client('s3')


def fetch_sailing_data():
    """
    Fetches sailing data from the API endpoint using the API key.
    """
    url = f"{SAILING_SITE}?apikey={API_KEY}"
    req = Request(url, headers={'User-Agent': 'AWS Lambda'})
    with urlopen(req) as response:
        return json.loads(response.read())


def fetch_weather_data(latitude, longitude):
    """
    Fetches weather data for the given latitude and longitude.
    """
    url = (
        f"{WEATHER_API_URL}?latitude={latitude}&longitude={longitude}"
        "&current=temperature_2m,weather_code,pressure_msl,surface_pressure,"
        "wind_speed_10m,wind_direction_10m,wind_gusts_10m&wind_speed_unit=kn&forecast_days=1&models=best_match"
    )
    req = Request(url, headers={'User-Agent': 'AWS Lambda'})
    with urlopen(req) as response:
        data = json.loads(response.read())
        #print(f"Weather data for {latitude}, {longitude}: {data}")  # Log the data
        return data


def combine_data(sailing_data):
    """
    Combines sailing data with weather data for each sailor.
    """
    combined_data = []
    for sailor in sailing_data['latestdata']['data']:
        try:
            # Parse latitude and longitude
            lat, lon = parse_coordinates(sailor['Latitude'], sailor['Longitude'])

            # Fetch weather data
            weather_data = fetch_weather_data(lat, lon)
            if 'current' not in weather_data:
                print(f"No weather data for {sailor['Boat']} at {lat}, {lon}")
                weather_data = {}  # Set default empty weather data if missing

            # Merge data
            sailor_data = {
                **sailor,
                "Weather": weather_data.get('current', {})
            }
            combined_data.append(sailor_data)
        except Exception as e:
            print(f"Failed to fetch weather for {sailor['Boat']}: {e}")
    return combined_data


def parse_coordinates(latitude, longitude):
    """
    Converts latitude and longitude from DMS (Degrees, Minutes, Seconds) format to decimal degrees.
    """
    def dms_to_decimal(dms):
        try:
            # Check if the input contains a degree symbol and a direction
            parts = dms.split('°')
            degrees = float(parts[0])
            minutes = float(parts[1].split("'")[0])
            direction = parts[1].split("'")[1].strip()[-1]  # Last character is the direction (N/S/E/W)
            
            # Calculate decimal degrees
            decimal = degrees + (minutes / 60)

            # Adjust for South or West by making the value negative
            if direction in ['S', 'W']:
                decimal = -decimal

            return decimal
        except Exception as e:
            raise ValueError(f"Error parsing coordinate {dms}: {e}")

    # Convert both latitude and longitude to decimal
    lat_decimal = dms_to_decimal(latitude)
    lon_decimal = dms_to_decimal(longitude)

    return lat_decimal, lon_decimal

    
def save_to_s3(data):
    """
    Saves the combined data as a JSON file in the specified S3 bucket.
    """
    filename = f"combined_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    s3_client.put_object(
        Bucket=BUCKET_NAME,
        Key=filename,
        Body=json.dumps(data, indent=4),
        ContentType='application/json'
    )
    print(f"Combined data saved to S3 bucket '{BUCKET_NAME}' as '{filename}'")


def lambda_handler(event, context):
    """
    AWS Lambda entry point.
    """
    try:
        # Fetch sailing data
        sailing_data = fetch_sailing_data()

        # Combine data with weather information
        combined_data = combine_data(sailing_data)

        # Save the combined data to S3
        save_to_s3(combined_data)
    except Exception as e:
        print(f"Error: {e}")
        raise
    finally:
        print(f"Execution completed at {datetime.now()}")
