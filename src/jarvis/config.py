import os
from pathlib import Path
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(), override=True)

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
WORKSPACE_DIR = BASE_DIR / "workspace"
DATASETS_DIR = WORKSPACE_DIR / "datasets"
RAW_DATASETS_DIR = BASE_DIR / "raw_datasets"
SYSTEM_PROMPT_DIR = BASE_DIR / "system_prompt"
MEMORY_DIR = WORKSPACE_DIR / "memory"

# Subdirectories
EMAIL_ARCHIVE_DIR = "email_archive"
MEETING_TRANSCRIPTS_DIR = "meeting_transcripts"

# API Keys (Loaded from environment)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LITELLM_API_KEY = os.getenv("LITELLM_API_KEY")
LITELLM_URL = os.getenv("LITELLM_URL", "https://ete-litellm.ai-models.vpc-int.res.ibm.com")
WATSONX_API_KEY = os.getenv("WATSONX_API_KEY")
WATSONX_URL = os.getenv("WATSONX_URL")
WATSONX_PROJECT_ID = os.getenv("WATSONX_PROJECT_ID")

# Heartbeat Configuration
HEARTBEAT_INTERVAL_MINUTES = 30
HEARTBEAT_PROMPT = (
    "Read HEARTBEAT.md if it exists (workspace context). "
    "Follow it strictly. Do not infer or repeat old tasks from prior chats. "
    "If nothing needs attention, reply HEARTBEAT_OK."
)
NO_REPLY_TOKEN = "NO_REPLY"
HEARTBEAT_OK_TOKEN = "HEARTBEAT_OK"
NEED_USER_ATTENTION_TOKEN = "NEED_USER_ATTENTION"

# Vector Store Config
VECTOR_STORE_PATH = BASE_DIR / "chroma_db"

