import logging
import yaml
from telegram.ext import ApplicationBuilder, CommandHandler
from bot import list_subscriptions, sub, unsub, fetch_rss_updates_periodically

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def load_config():
    """Load the configuration from the config.yml file."""
    try:
        with open('config.yml', 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        logger.error("Configuration file 'config.yml' not found.")
        raise
    except yaml.YAMLError as e:
        logger.error("Error parsing 'config.yml': %s", e)
        raise


def create_bot_application(token):
    """Create and return the Telegram bot application."""
    try:
        app = ApplicationBuilder().token(token).build()
        return app
    except Exception as e:
        logger.error("Error creating the Telegram bot application: %s", e)
        raise


def add_command_handlers(app):
    """Add command handlers to the bot application."""
    app.add_handler(CommandHandler("list", list_subscriptions))
    app.add_handler(CommandHandler("sub", sub))
    app.add_handler(CommandHandler("unsub", unsub))


def schedule_jobs(app, chat_id):
    """Schedule periodic jobs for the bot."""
    job_queue = app.job_queue
    job_queue.run_repeating(fetch_rss_updates_periodically,
                            interval=60, first=0, chat_id=chat_id)


def main():
    try:
        config = load_config()
        BOT_TOKEN = config['bot_token']
        CHAT_ID = config['chat_id']

        app = create_bot_application(BOT_TOKEN)
        add_command_handlers(app)
        schedule_jobs(app, CHAT_ID)

        logger.info("Bot is starting...")
        app.run_polling()
    except Exception as e:
        logger.error("Failed to start the bot: %s", e)


if __name__ == '__main__':
    main()
