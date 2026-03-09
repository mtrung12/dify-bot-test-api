import os
from dotenv import load_dotenv
import requests 
import time

load_dotenv()

api_url = "https://api.dify.ai/v1/chat-messages"

def call_dify_api(conversation_id, query, api_key):
    if api_key is None:
        raise ValueError("API key is missing for the request.")
    payload = {
        'query': query,  
        'inputs': {},  
        'response_mode': 'blocking',  
        'user': 'test_user',  
        'conversation_id': conversation_id if conversation_id else "",  
    }

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }

    for attempt in range(3):  
        response = requests.post(api_url, json=payload, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data.get('event') == 'message':
                return data.get('answer'), data.get('conversation_id')
            else:
                raise ValueError(f"Unexpected event in response: {data.get('event')}")
        elif response.status_code in [400, 404, 500]:
            error_data = response.json()
            raise ValueError(f"Dify API error ({response.status_code}): {error_data.get('code', 'unknown')} - {error_data.get('message', 'unknown')}")
        else:
            time.sleep(1)  

    raise ValueError(f"Dify API failed after retries: {response.text}")