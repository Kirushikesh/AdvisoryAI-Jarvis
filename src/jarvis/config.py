import os
from pathlib import Path
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(), override=True)

# Base Paths
# When installed via `pip install .` in Docker, __file__ resolves into site-packages.
# APP_DIR env var (set to /app in Dockerfile) pins the project root correctly.
_file_based_root = Path(__file__).resolve().parent.parent.parent
BASE_DIR = Path(os.getenv("APP_DIR", str(_file_based_root)))
WORKSPACE_DIR = BASE_DIR / "workspace"
DATASETS_DIR = WORKSPACE_DIR / "datasets"
CLIENT_DATA_PATH = DATASETS_DIR  # Alias for file_monitor tool
RAW_DATASETS_DIR = BASE_DIR / "raw_datasets"
SYSTEM_PROMPT_DIR = BASE_DIR / "system_prompt"
MEMORY_DIR = WORKSPACE_DIR / "memory"
EMAIL_ARCHIVE_DIR = BASE_DIR / "email_archive"  # Owned by the Calendar MCP server


# API Keys (Loaded from environment)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LITELLM_API_KEY = os.getenv("LITELLM_API_KEY")
LITELLM_URL = os.getenv("LITELLM_URL", "https://ete-litellm.ai-models.vpc-int.res.ibm.com")
WATSONX_API_KEY = os.getenv("WATSONX_API_KEY")
WATSONX_URL = os.getenv("WATSONX_URL")
WATSONX_PROJECT_ID = os.getenv("WATSONX_PROJECT_ID")

# Heartbeat Configuration
HEARTBEAT_INTERVAL_MINUTES = int(os.getenv("HEARTBEAT_INTERVAL_MINUTES", 30))
HEARTBEAT_PROMPT = (
    "Read HEARTBEAT.md if it exists (workspace context). "
    "Follow it strictly. Do not infer or repeat old tasks from prior chats. "
    "If nothing needs attention, reply HEARTBEAT_OK."
)
NO_REPLY_TOKEN = "NO_REPLY"
HEARTBEAT_OK_TOKEN = "HEARTBEAT_OK"

# Vector Store Config
VECTOR_STORE_PATH = BASE_DIR / "chroma_db"

