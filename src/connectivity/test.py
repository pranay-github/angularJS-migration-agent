from chain import get_copilot_token_via_internal_endpoint;

token = get_copilot_token_via_internal_endpoint();
print(f'✅ Token acquired!: {token}' if token else '❌ Failed')