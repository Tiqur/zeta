import os
import json
import requests
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get configuration from environment variables
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
API_URL = os.getenv('API_URL', 'https://api.deepseek.com/v1/chat/completions')
MATH_TOPIC = os.getenv('MATH_TOPIC')

# Validate required environment variables
def validate_config():
    if not DEEPSEEK_API_KEY:
        print("ERROR: DeepSeek API key not found in environment variables.")
        print("Please set DEEPSEEK_API_KEY in your .env file or environment.")
        sys.exit(1)

    if not MATH_TOPIC:
        print("ERROR: Math topic not found in environment variables.")
        print("Please set MATH_TOPIC in your .env file or environment.")
        sys.exit(1)

    return MATH_TOPIC

# Function to make an API call to DeepSeek
def call_deepseek_api(prompt, expect_json=False):
    try:
        request_body = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.5
        }
        
        # Only add the response_format if we're expecting JSON
        if expect_json:
            request_body["response_format"] = {"type": "json_object"}
        
        response = requests.post(
            API_URL,
            json=request_body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
            }
        )
        
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.json()["choices"][0]["message"]["content"]
    
    except requests.exceptions.RequestException as e:
        print(f"API Call Error: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response Status: {e.response.status_code}")
            print(f"Response Body: {e.response.text}")
        sys.exit(1)

# Function to save data to JSON file
def save_to_json(data, filename):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving data to {filename}: {str(e)}")
        return False

# Function to save text to file
def save_to_text(data, filename):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(data)
        return True
    except Exception as e:
        print(f"Error saving text to {filename}: {str(e)}")
        return False

# Function to load data from JSON file
def load_from_json(filename):
    try:
        if not os.path.exists(filename):
            print(f"ERROR: File not found: {filename}")
            return None
        
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data
    except Exception as e:
        print(f"Error loading data from {filename}: {str(e)}")
        return None

