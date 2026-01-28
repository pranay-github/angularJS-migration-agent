Connectivity:

Steps to attain Auth code for VSCODE :
 
Step 1: Open Powershell 
Run:
curl -X POST https://github.com/login/device/code -H "Accept: application/json" -d "client_id=01ab8ac9400c4e429b23&scope=user:email"   
Output:
{"device_code":"5c12f2c57919db7f75c1a2e2fdcce1","user_code":"AF11-3ABA","verification_uri":"https://github.com/login/device","expires_in":899,"interval":5}
Copy: 1. user_code  2.device_code

Step 2:
Open Link: https://github.com/login/device
Authorize using user_code from above step and paste here
 

Step 3:
Replace device_code with code copied in Step 1 in below command.

Run Command:
curl -X POST https://github.com/login/oauth/access_token -H "Accept: application/json" -d  "client_id=01ab8ac9400c4e429b23&device_code=d2a32d071e85e5e73c54e8012c546d9541289f1b&grant_type=urn:ietf:params:oauth:grant-type:device_code"
 
Output :
{"access_token":"{{TOKEN}}","token_type":"bearer","scope":"user:email"}

Step 4:

In command prompt Set Environment variable [session]:
$env:GITHUB_TOKEN = "{{TOKEN}}"

Install:
py -m pip install requests langchain langchain-core langchain-community


What This Code Does? [chain.py]

This file creates a bridge between GitHub Copilot's API and Python's LangChain framework, allowing you to use Copilot (with access to GPT-4, Claude, etc.) in agent-based applications.

Three Main Components:

1. Token Authentication (Lines 98-112)
def get_copilot_token_via_internal_endpoint()

What it does:

Takes your GitHub token (GITHUB_TOKEN from environment)
Calls https://api.github.com/copilot_internal/v2/token
Gets a temporary Copilot API token (valid ~8 hours)
This lets you access Copilot's paid models without separate API keys

Why: GitHub Copilot subscription includes access to multiple AI models, this function unlocks that access.

2. Raw API Client (Lines 17-82 & 114-170)

CopilotLLM (Basic version)
Simple REST client for Copilot Chat API
Sends messages, gets text responses
No tool calling support

ToolEnabledCopilotLLM (Advanced version)
Extends basic client with function/tool calling
Mimics VS Code headers to authenticate properly
Converts tool definitions to OpenAI format
Returns full JSON (including tool calls, not just text)

Key method: invoke_raw() - sends requests to https://api.business.githubcopilot.com/chat/completions

3. LangChain Adapter (Lines 172-263)
Purpose: Makes Copilot API compatible with LangChain's agent framework

Key Features:

A. Tool Binding (Line 182-184)

def bind_tools(self, tools):

Lets agents call Python functions
Converts LangChain tool definitions → OpenAI format
Required for [agent 2.py](c:\Users\tejap\OneDrive - OpenText\Documents\Learning\Learning AI\Coding\migration-agent\connectivity\agent 2.py) to work

B. Vision Support (Lines 186-213)
def _convert_content(self, content):

Handles image inputs (screenshots, diagrams)
Fixes nested image_url structure
Ensures Copilot receives images correctly

C. Message Translation (Lines 215-263)
def _generate(self, messages):

Converts LangChain messages → OpenAI format
Handles: System, Human, AI, Tool messages
Parses tool calls from responses
Returns structured ChatResult

How it all works:
┌─────────────────────────────────────────────────────────┐
│  1. Your GitHub Token (from device flow)               │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│  2. get_copilot_token_via_internal_endpoint()          │
│     └─> Exchanges for Copilot API token                │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│  3. ChatCopilot(token=token, model="claude-3.5-sonnet")│
│     └─> Creates LangChain-compatible LLM               │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│  4. Agent uses it with tools (from agent 2.py)         │
│     • Calls functions                                   │
│     • Analyzes images                                   │
│     • Self-corrects code                                │
└─────────────────────────────────────────────────────────┘

Archietecture [Migration Agent]:

┌─────────────────────────────────────────────────────────────┐
│                    Migration Pipeline                        │
└─────────────────────────────────────────────────────────────┘

1️⃣ INPUT: api.js (AngularJS 1.x code with $resource)
   ↓
2️⃣ CLASSIFIER (LLM):
   → Type: "service"
   → Features: uses_resource = true
   → Complexity: "high"
   → Strategy: "service_with_httpclient"
   ↓
3️⃣ PATTERN REGISTRY:
   → Loads migration rules from patterns.json
   → Builds structured prompt with:
     - Source code
     - 5 migration rules
     - Detected features
     - Output requirements
   ↓
4️⃣ MIGRATION ENGINE (GitHub Copilot - claude-sonnet-4):
   → Receives: SystemMessage + HumanMessage
   → Generates: Angular 16+ TypeScript code
   → Uses: HttpClient, @Injectable, Observables
   ↓
5️⃣ VALIDATOR:
   → TypeScript check: ⚠️ tsc not installed (bypassed)
   → Angular patterns: ✅ All good
   → Code quality: 💡 3 suggestions
   → Score: 81/100 (GOOD)
   ↓
6️⃣ OUTPUT: api.service.ts
   → Modern Angular 16+ service
   → 7,679 characters
   → Uses inject(), HttpClient, Observables