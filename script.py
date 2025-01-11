import os
import json
from datetime import datetime
from urllib.request import Request, urlopen
import boto3

# Environment variables
API_KEY = os.environ['api_key']  # API key stored in the environment variable
SITE = os.environ['site']  # API endpoint stored in the environment variable
BUCKET_NAME = os.environ['bucket_name']  # S3 bucket name stored in the environment variable

s3_client = boto3.client('s3')

def fetch_data():
    """
    Fetches data from the API endpoint using the API key.
    """
    # Add the API key to the URL
    url = f"{SITE}?apikey={API_KEY}"
    req = Request(url, headers={'User-Agent': 'AWS Lambda'})
    
    # Fetch the response
    with urlopen(req) as response:
        data = response.read()
        return data

def save_to_s3(data):
    """
    Saves the API response as a JSON file in the specified S3 bucket.
    """
    # Generate filename based on the current timestamp
    # needs to be fixed later due to the different time zones used
    filename = f"api_response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    # Upload the file to S3
    s3_client.put_object(
        Bucket=BUCKET_NAME,
        Key=filename,
        Body=json.dumps(json.loads(data), indent=4),
        ContentType='application/json'
    )
    print(f"Response saved to S3 bucket '{BUCKET_NAME}' as '{filename}'")

def lambda_handler(event, context):
    # the idea is to have this run 6 times per day 
    # 07:00 11:00 15:00 19:00 23:00 03:00 (the times the sailboats give us an update on their position)
    try:
        data = fetch_data()        
        save_to_s3(data)
        
    except Exception as e:
        raise
    finally:
        print(f"Check complete at {str(datetime.now())}")