import os
import json
import requests
import sys
import sqlite3
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
            "temperature": 0.5,
            "max_tokens": 4000  # Ensure we get complete responses
        }
        
        # Add response_format if we're expecting JSON
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
        
        # Check for HTTP errors
        response.raise_for_status()
        
        # Get the content from the response
        response_json = response.json()
        content = response_json["choices"][0]["message"]["content"]
        
        # If we're expecting JSON, try to parse it
        if expect_json:
            try:
                # First, clean the content in case there's any prefixes or suffixes
                # Sometimes LLMs add markdown code blocks or explanatory text
                content = clean_json_response(content)
                return json.loads(content)
            except json.JSONDecodeError:
                # If parsing fails, return the raw content
                print("Warning: Expected JSON but could not parse response. Returning raw content.")
                return content
        
        # Otherwise return the raw content
        return content
    
    except requests.exceptions.RequestException as e:
        print(f"API Call Error: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response Status: {e.response.status_code}")
            print(f"Response Body: {e.response.text}")
        sys.exit(1)

def clean_json_response(response):
    """
    Clean the JSON response by removing any non-JSON content.
    Sometimes LLMs add markdown code blocks or explanatory text.
    """
    # Look for JSON content within triple backticks
    if '```json' in response and '```' in response:
        start = response.find('```json') + 7
        end = response.find('```', start)
        return response[start:end].strip()
    
    # Look for JSON content within single backticks
    if '`{' in response and '}`' in response:
        start = response.find('`{') + 1
        end = response.find('}`', start) + 1  # Include the closing brace
        return response[start:end].strip()
    
    # Try to find the outermost JSON object
    if '{' in response and '}' in response:
        start = response.find('{')
        # Find the matching closing brace
        brace_count = 0
        for i in range(start, len(response)):
            if response[i] == '{':
                brace_count += 1
            elif response[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    end = i + 1
                    return response[start:end].strip()
    
    # If all else fails, return the original response
    return response

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

# Database utility functions
def get_db_connection():
    """Create a connection to the SQLite database"""
    conn = sqlite3.connect('problems.db')
    return conn

def execute_query(query, params=(), fetch_one=False, fetch_all=False):
    """Execute a query and optionally fetch results"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    
    result = None
    if fetch_one:
        result = cursor.fetchone()
    elif fetch_all:
        result = cursor.fetchall()
    else:
        conn.commit()
    
    conn.close()
    return result
