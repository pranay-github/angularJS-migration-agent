import sys
from pathlib import Path
# sys.path.insert(0, str(Path(__file__).parent.parent / "connectivity"))

from connectivity import get_copilot_token_via_internal_endpoint
import requests

def get_available_models(api_token):
    url = "https://api.business.githubcopilot.com/models"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Accept": "application/json",
        "copilot-integration-id": "vscode-chat",
        "editor-plugin-version": "copilot-chat/0.32.1",
        "editor-version": "vscode/1.96.0",
        "user-agent": "GitHubCopilotChat/0.32.1"
    }
    
    response = requests.get(url, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text[:500]}")
    
    if response.status_code == 200:
        models = response.json()
        return models
    return []

# Get Copilot token and fetch models
token = get_copilot_token_via_internal_endpoint()
if token:
    print("🔑 Token acquired!")
    print("\n📋 Fetching available models...\n")
    models = get_available_models(token)
    if models:
        print("Available models:")
        if isinstance(models, dict) and 'data' in models:
            for m in models['data']:
                print(f"  - {m.get('id', m)}")
        else:
            print(models)
else:
    print("❌ Failed to get Copilot token")