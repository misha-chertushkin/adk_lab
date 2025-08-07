# file: test_client.py

import requests
import json

url = "http://localhost:8001/stackexchange/invoke"
query = "How do I fix a '422 Unprocessable Entity' error in FastAPI?"

payload = {
    "input": {
        "messages": [
            # THE FIX: Change "type": "user" to "type": "human"
            {"type": "human", "content": query}
        ]
    }
}

# ... (the rest of the script remains the same) ...

print(f"▶️  Attempting to call server at: {url}")
print(f"▶️  Sending payload:\n{json.dumps(payload, indent=2)}")

try:
    response = requests.post(url, json=payload, timeout=30)
    print("\n--- SERVER RESPONSE ---")
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("\n✅ Success! Server responded with 200 OK.")
        print("Response JSON:")
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"\n❌ Error! Server responded with status code {response.status_code}.")
        print("Response Body:")
        try:
            print(json.dumps(response.json(), indent=2))
        except json.JSONDecodeError:
            print(response.text)
except requests.exceptions.RequestException as e:
    print(f"\nCLIENT-SIDE ERROR: An error occurred while trying to make the request.")
    print(e)