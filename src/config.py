# config.py
"""
Migration Engine Configuration
"""

# LLM Model Configuration
DEFAULT_MODEL = "gpt-5-mini"
AVAILABLE_MODELS = [
    "claude-sonnet-4",
    "gpt-4o",
    "gpt-4",
    "gpt-5-mini"
]

# Other settings
MAX_CODE_SIZE = 10000
FALLBACK_CODE_SIZE = 5000
DEFAULT_FILE_EXTENSIONS = ['.js', '.html', '.ts']