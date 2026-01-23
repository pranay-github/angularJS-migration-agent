"""
AngularJS to Angular 16 Migration Agent
Uses GitHub Copilot (Claude 3.5 Sonnet) via your subscription
"""

import os
import sys
from pathlib import Path

# Add connectivity folder to path
# sys.path.insert(0, str(Path(__file__).parent.parent / "connectivity"))

from connectivity import ChatCopilot, get_copilot_token_via_internal_endpoint
from langchain_core.messages import HumanMessage, SystemMessage

def load_migration_rules():
    """Load migration rules from prompts file"""
    rules_path = Path(__file__).parent / "prompts" / "angularjs-to-angular.txt"
    if not rules_path.exists():
        return """
You are an expert Angular migration specialist.
Convert AngularJS (1.x) code to Angular 16+ using:
- Standalone Components (no NgModules)
- TypeScript with strict typing
- HttpClient instead of $http
- RxJS for async operations
- Signals for reactive state (Angular 16+)

Rules:
1. Convert $resource to HttpClient service
2. Replace $scope with component class properties
3. Use Angular Router instead of ui-router
4. Convert services to injectable classes with providedIn: 'root'
5. Use modern Angular lifecycle hooks
"""
    return rules_path.read_text(encoding='utf-8')


def load_legacy_code(filename: str):
    """Load legacy AngularJS code"""
    code_path = Path(__file__).parent / "legacy-code" / filename
    if not code_path.exists():
        raise FileNotFoundError(f"Legacy code file not found: {code_path}")
    return code_path.read_text(encoding='utf-8')


def save_migrated_code(content: str, filename: str):
    """Save migrated Angular code"""
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    
    output_name = filename.replace('.js', '.service.ts')
    output_path = output_dir / output_name
    
    output_path.write_text(content, encoding='utf-8')
    print(f"✅ Migrated code saved to: {output_path}")


def run_migration(filename: str, model: str = "claude-sonnet-4"):
    """
    Main migration function
    
    Args:
        filename: Legacy AngularJS file to migrate
        model: AI model to use (claude-3.5-sonnet, claude-sonnet-4.5, o1-preview)
    """
    print(f"🚀 Starting migration for: {filename}")
    print(f"🤖 Using model: {model}")
    
    # Step 1: Get Copilot token
    print("🔑 Acquiring Copilot token...")
    token = get_copilot_token_via_internal_endpoint()
    if not token:
        print("❌ Failed to get token. Set GITHUB_TOKEN environment variable.")
        return
    
    # Step 2: Initialize ChatCopilot
    print(f"🔧 Initializing {model}...")
    llm = ChatCopilot(token=token, model=model)
    
    # Step 3: Load files
    print("📂 Loading migration rules and legacy code...")
    rules = load_migration_rules()
    legacy_code = load_legacy_code(filename)
    
    # Step 4: Create migration prompt
    prompt_text = f"""Migrate this AngularJS code to Angular 16:

{legacy_code}

Requirements:
1. Use Angular 16+ Standalone Components
2. Convert $resource to HttpClient service
3. Use TypeScript with proper types
4. Include all necessary imports
5. Add JSDoc comments
6. Return ONLY the migrated TypeScript code, no explanations"""
    
    messages = [
        SystemMessage(content=rules),
        HumanMessage(content=prompt_text)
    ]
    
    # Step 5: Get AI response
    print("🧠 Processing migration with AI...")
    response = llm.invoke(messages)
    
    # Step 6: Clean and save code
    migrated_code = response.content
    
    if "```typescript" in migrated_code:
        migrated_code = migrated_code.split("```typescript")[1].split("```")[0].strip()
    elif "```ts" in migrated_code:
        migrated_code = migrated_code.split("```ts")[1].split("```")[0].strip()
    elif "```" in migrated_code:
        migrated_code = migrated_code.split("```")[1].split("```")[0].strip()
    
    save_migrated_code(migrated_code, filename)
    
    print("\n" + "="*60)
    print("📊 Migration Summary:")
    print(f"   Input:  legacy-code/{filename}")
    print(f"   Output: output/{filename.replace('.js', '.service.ts')}")
    print(f"   Model:  {model}")
    print(f"   Size:   {len(migrated_code)} characters")
    print("="*60)


if __name__ == "__main__":
    # Use Claude Sonnet 4 (confirmed working)
    run_migration("api.js", model="claude-sonnet-4")