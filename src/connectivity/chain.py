
import os
import sys
import json
import shlex
import argparse
import textwrap
import asyncio
import shutil
from typing import Dict, Any, List, Optional

import requests


COPILOT_CHAT_URL = "https://api.business.githubcopilot.com/chat/completions"

class CopilotLLM:
    """
    Minimal wrapper around the Copilot Chat REST endpoint (non-streaming).
    """

    def __init__(self, token: str, model: str = "gpt-4.1", timeout: int = 60):
        if not token:
            raise ValueError("Copilot token is empty. Set COPILOT_TOKEN or pass --token.")
        self.token = token
        self.model = model
        self.timeout = timeout

    def _headers(self) -> Dict[str, str]:
        # Keep headers minimal; do not spoof editor internals.
        return {
            "authorization": f"Bearer {self.token}",
            "content-type": "application/json",
            "copilot-integration-id": "vscode-chat",
            "editor-plugin-version": "copilot-chat/0.32.1",
            "editor-version": "vscode/1.105.0",
            "openai-intent": "conversation-agent",
            "user-agent": "GitHubCopilotChat/0.32.1",
            "vscode-machineid": "60c996423c869f575fa4dd8886b167f8e6525788fbf5d7c1ffba8b0a0d0ed9ce",
            "vscode-sessionid": "cf23e856-4de4-498b-8800-b1e4791843681760498800987",
            "x-github-api-version": "2025-08-20",
            "x-initiator": "user",
            "x-interaction-id": "92a10709-ff6c-4b23-9ef5-59f1304fa0d4",
            "x-interaction-type": "conversation-agent",
            "x-request-id": "2afd47cc-fee9-409e-8120-23209f8c903a",
            "x-vscode-user-agent-library-version": "electron-fetch",
            "sec-fetch-site": "none",
            "sec-fetch-mode": "no-cors",
            "sec-fetch-dest": "empty",
            "accept-encoding": "gzip, deflate, br, zstd",
            "priority": "u=4, i",
            "copilot-vision-request": "true",
        }

    def invoke(self, messages: List[Dict[str, str]], max_tokens: int = 2048, temperature: float = 0.0) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "top_p": 1,
            "max_tokens": max_tokens,
            "stream": False,
        }


        resp = requests.post(COPILOT_CHAT_URL, headers=self._headers(), json=payload, timeout=self.timeout)
        try:
            resp.raise_for_status()
            
        except requests.HTTPError as e:
            raise RuntimeError(f"Copilot API error: HTTP {resp.status_code} - {resp.text[:500]}") from e

        data = resp.json()
        print(data)
        try:
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            raise RuntimeError(f"Unexpected Copilot response: {json.dumps(data)[:800]}") from e

    def bind(self, **kwargs):
        # Return self for compatibility
        return self
import os
import uuid
import json
import requests
from typing import Any, List, Dict, Optional, Sequence, Union

# --- CRITICAL IMPORTS ---
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.outputs import ChatResult, ChatGeneration
from langchain_core.tools import BaseTool
from langchain_core.utils.function_calling import convert_to_openai_tool
from pydantic import Field, PrivateAttr
from langchain_core.runnables import Runnable

# --- 1. TOKEN FETCHER ---
def get_copilot_token_via_internal_endpoint(timeout: int = 30) -> Optional[str]:
    if os.environ.get('COPILOT_TOKEN'):
        return os.environ.get('COPILOT_TOKEN')
    gh_token = os.environ.get('GITHUB_TOKEN')
    if not gh_token:
        print("(!) GITHUB_TOKEN is missing.")
        return None
    try:
        url = "https://api.github.com/copilot_internal/v2/token"
        headers = {"authorization": f"token {gh_token}", "user-agent": "GitHubCopilotChat/0.32.1"}
        r = requests.get(url, headers=headers, timeout=timeout)
        r.raise_for_status()
        return r.json().get("token")
    except Exception as e:
        print(f"(!) Failed to fetch internal token: {e}")
        return None

# --- 2. RAW CLIENT ---
class ToolEnabledCopilotLLM:
    def __init__(self, token: str, model: str = "gpt-4o"):
        self.token = token
        self.model = model
        self._session_id = str(uuid.uuid4())
        self._machine_id = str(uuid.uuid4().hex)

    def _headers(self) -> Dict[str, str]:
        return {
            "authorization": f"Bearer {self.token}",
            "content-type": "application/json",
            "copilot-integration-id": "vscode-chat",
            "editor-plugin-version": "copilot-chat/0.32.1",
            "editor-version": "vscode/1.96.0",
            "openai-intent": "conversation-agent",
            "user-agent": "GitHubCopilotChat/0.32.1",
            "vscode-machineid": self._machine_id,
            "vscode-sessionid": self._session_id,
            "copilot-vision-request": "true" 
        }

    def invoke_raw(self, messages: List[Dict[str, str]], tools: Optional[List[Dict]] = None, **kwargs) -> Dict:
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.1),
            "stream": False,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        url = "https://api.business.githubcopilot.com/chat/completions"
        resp = requests.post(url, headers=self._headers(), json=payload, timeout=60)
        
        if resp.status_code != 200:
            print(f"\n[API ERROR {resp.status_code}] Body: {resp.text[:200]}\n")
            
        resp.raise_for_status()
        return resp.json()

# --- 3. LANGCHAIN ADAPTER ---
class ChatCopilot(BaseChatModel):
    _client: ToolEnabledCopilotLLM = PrivateAttr()
    model_name: str = Field(default="gpt-4o", alias="model")

    def __init__(self, token: str, model: str = "gpt-4o", **kwargs):
        super().__init__(**kwargs)
        self._client = ToolEnabledCopilotLLM(token=token, model=model)

    def bind_tools(self, tools: Sequence[Any], **kwargs: Any) -> Runnable[Any, BaseMessage]:
        formatted_tools = [convert_to_openai_tool(tool) for tool in tools]
        return self.bind(tools=formatted_tools, **kwargs)

    def _convert_content(self, content: Any) -> Any:
        """
        Converts LangChain content to OpenAI/Copilot content.
        Crucially: Ensures image_url is NOT flattened to a string.
        """
        if isinstance(content, str):
            return content
        
        if isinstance(content, list):
            formatted = []
            for item in content:
                if isinstance(item, dict):
                    # Handle Image Types
                    if item.get("type") == "image_url":
                        img_val = item.get("image_url")
                        
                        # Case A: {"type": "image_url", "image_url": "data:..."} -> Fix nesting
                        if isinstance(img_val, str):
                            formatted.append({
                                "type": "image_url", 
                                "image_url": {"url": img_val}
                            })
                        # Case B: {"type": "image_url", "image_url": {"url": "..."}} -> Keep as is
                        elif isinstance(img_val, dict) and "url" in img_val:
                            formatted.append(item)
                        # Case C: Bad format -> Try to fix
                        else:
                            formatted.append(item)
                    else:
                        formatted.append(item)
            return formatted
        return str(content)

    def _generate(self, messages: List[BaseMessage], stop: Optional[List[str]] = None, **kwargs: Any) -> ChatResult:
        openai_msgs = []
        for m in messages:
            if isinstance(m, SystemMessage):
                openai_msgs.append({"role": "system", "content": m.content})
            elif isinstance(m, HumanMessage):
                # Apply strict conversion
                openai_msgs.append({"role": "user", "content": self._convert_content(m.content)})
            elif isinstance(m, AIMessage):
                msg = {"role": "assistant", "content": m.content or ""}
                if m.tool_calls:
                    msg["tool_calls"] = [
                        {"id": tc["id"], "type": "function", "function": {"name": tc["name"], "arguments": json.dumps(tc["args"])}}
                        for tc in m.tool_calls
                    ]
                openai_msgs.append(msg)
            elif isinstance(m, ToolMessage):
                openai_msgs.append({"role": "tool", "tool_call_id": m.tool_call_id, "content": m.content})

        tools = kwargs.pop("tools", None)
        response = self._client.invoke_raw(openai_msgs, tools=tools, **kwargs)
        
        choice = response["choices"][0]
        msg_data = choice["message"]
        content = msg_data.get("content") or ""
        
        tool_calls = []
        if "tool_calls" in msg_data:
            for tc in msg_data["tool_calls"]:
                tool_calls.append({
                    "name": tc["function"]["name"],
                    "args": json.loads(tc["function"]["arguments"]),
                    "id": tc["id"]
                })
        
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=content, tool_calls=tool_calls))])

    @property
    def _llm_type(self) -> str:
        return "copilot-chat"
