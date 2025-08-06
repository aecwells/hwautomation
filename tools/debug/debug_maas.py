#!/usr/bin/env python3
"""
Debug script to test MAAS connection and identify the issue
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from hwautomation.utils.config import load_config
from hwautomation.maas.client import create_maas_client
import requests
from requests_oauthlib import OAuth1Session
from oauthlib.oauth1 import SIGNATURE_PLAINTEXT

def test_maas_connection():
    """Test MAAS connection with detailed debugging"""
    print("Loading configuration...")
    config_path = Path(__file__).parent / 'config.yaml'
    print(f"Config file path: {config_path}")
    print(f"Config file exists: {config_path.exists()}")
    
    config = load_config(str(config_path))
    
    if 'maas' not in config:
        print("ERROR: No MAAS configuration found in config.yaml")
        return
    
    maas_config = config['maas']
    print(f"MAAS Host: {maas_config.get('host')}")
    print(f"Consumer Key: {maas_config.get('consumer_key')}")
    print(f"Token Key: {maas_config.get('token_key')}")
    print(f"SSL Verification: {maas_config.get('verify_ssl', True)}")
    
    # Test basic connectivity first
    print("\n--- Testing basic connectivity ---")
    host = maas_config['host'].rstrip('/')
    test_url = f"{host}/api/2.0/"
    
    try:
        response = requests.get(test_url, timeout=10, verify=maas_config.get('verify_ssl', True))
        print(f"Status Code: {response.status_code}")
        print(f"Content Type: {response.headers.get('content-type', 'Unknown')}")
        print(f"Response Length: {len(response.text)}")
        print(f"Response Preview: {response.text[:200]}...")
    except Exception as e:
        print(f"Basic connectivity failed: {e}")
        return
    
    # Test with OAuth
    print("\n--- Testing OAuth authentication ---")
    try:
        session = OAuth1Session(
            maas_config['consumer_key'],
            resource_owner_key=maas_config['token_key'],
            resource_owner_secret=maas_config['token_secret'],
            signature_method=SIGNATURE_PLAINTEXT
        )
        
        machines_url = f"{host}/api/2.0/machines/"
        print(f"Requesting: {machines_url}")
        
        response = session.get(machines_url, verify=maas_config.get('verify_ssl', True))
        print(f"Status Code: {response.status_code}")
        print(f"Content Type: {response.headers.get('content-type', 'Unknown')}")
        print(f"Response Length: {len(response.text)}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"Successfully parsed JSON. Found {len(data)} machines.")
                return data
            except Exception as json_error:
                print(f"JSON parsing failed: {json_error}")
                print(f"Response content: {response.text[:500]}...")
        else:
            print(f"HTTP Error: {response.status_code}")
            print(f"Response: {response.text[:500]}...")
            
    except Exception as e:
        print(f"OAuth request failed: {e}")
    
    # Test using the client
    print("\n--- Testing with MaasClient ---")
    try:
        maas_client = create_maas_client(maas_config)
        machines = maas_client.get_machines()
        print(f"MaasClient returned {len(machines)} machines")
        return machines
    except Exception as e:
        print(f"MaasClient failed: {e}")

if __name__ == "__main__":
    test_maas_connection()
