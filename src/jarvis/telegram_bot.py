import os
import uuid
import logging
from dotenv import load_dotenv, find_dotenv

# Load env variables
load_dotenv(find_dotenv(), override=True)

from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

from jarvis.deepagent import create_jarvis_agent, init_calendar_tools, init_market_feed_tools
from jarvis.sub_agents.atlas import atlas_agent
from jarvis.sub_agents.emma import emma_agent
from jarvis.sub_agents.colin import colin_agent

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============================================================================
# Agent Management
# ============================================================================
_agents = {}

def get_or_create_agent(agent_type: str, thread_id: str):
    """Get or create an agent for the given thread."""
    key = f"{agent_type}:{thread_id}"

    if key not in _agents:
        logger.info(f"Creating new agent instance for {key}")
        if agent_type == "jarvis":
            _agents[key] = create_jarvis_agent()
        elif agent_type == "atlas":
            _agents[key] = atlas_agent
        elif agent_type == "emma":
            _agents[key] = emma_agent
        elif agent_type == "colin":
            _agents[key] = colin_agent
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")

    return _agents[key]

# ── Message parser ───────────────────────────────────────────────────
def parse_message(text: str):
    """
    Parses '@agentname actual message here'
    Returns (agent_name, message) or (None, None)
    """
    parts = text.strip().split(maxsplit=1)
    if not parts:
        return None, None
    
    agent_key = parts[0].lower()
    if agent_key.startswith("@"):
        agent_name = agent_key[1:]
        if agent_name in ["jarvis", "atlas", "emma", "colin"]:
            message = parts[1] if len(parts) > 1 else ""
            return agent_name, message
            
    return None, None

# ── Telegram message handler ─────────────────────────────────────────
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    chat_id = update.message.chat_id

    agent_name, user_message = parse_message(text)

    if not agent_name:
        await update.message.reply_text(
            "Unknown agent or missing '@'. Try: @jarvis, @atlas, @emma, @colin"
        )
        return

    # Acknowledge receipt
    await update.message.reply_text(
        f"⏳ {agent_name.capitalize()} is working on it..."
    )

    # Use chat_id as a persistent thread_id for continuity in conversation
    thread_id = str(chat_id)

    try:
        agent = get_or_create_agent(agent_name, thread_id)
        config = {"configurable": {"thread_id": thread_id}}
        
        # Invoke the agent asynchronously
        result = await agent.ainvoke(
            {"messages": [("user", user_message)]},
            config
        )
        
        # Extract the AI's response text
        response_text = ""
        for msg in reversed(result.get("messages", [])):
            if hasattr(msg, "content") and getattr(msg, "type", "") == "ai":
                response_text = msg.content
                break
                
        if not response_text or response_text.strip() == "NO_REPLY":
            response_text = "I don't have anything to add at this moment."
            
        await update.message.reply_text(response_text)
        
    except Exception as e:
        logger.error("Error during agent execution", exc_info=True)
        await update.message.reply_text(f"❌ Error: {str(e)}")

# ── Bot Initialization ───────────────────────────────────────────────
async def post_init(application: Application):
    """
    Hook that runs after the application is initialized and within the event loop.
    We warm up our MCP tools here because they require a running event loop.
    """
    logger.info("📅 Loading Calendar MCP tools...")
    await init_calendar_tools()
    logger.info("📅 Calendar MCP tools ready")

    logger.info("📈 Loading Market Feed MCP tools...")
    await init_market_feed_tools()
    logger.info("📈 Market Feed MCP tools ready")

def main():
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        logger.error("❌ TELEGRAM_BOT_TOKEN not found in .env. Please set it.")
        return
        
    app = Application.builder().token(bot_token).post_init(post_init).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("✅ Telegram Bot is running. Send messages like: @jarvis what is the weather?")
    app.run_polling()

if __name__ == "__main__":
    main()
