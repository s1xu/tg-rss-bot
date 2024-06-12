import yaml
import logging
from telegram.ext import ApplicationBuilder, CommandHandler, filters, MessageHandler
from bot import *

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def load_config() -> dict:
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


def create_bot_application(config: dict):
    """Create and return the Telegram bot application."""
    try:
        BOT_TOKEN = config.get('bot_token')
        if not BOT_TOKEN:
            raise ValueError("Bot token is missing in the configuration.")

        app_builder = ApplicationBuilder().token(BOT_TOKEN)

        BASE_URL = config.get('endpoint')
        if BASE_URL:
            app_builder.base_url(BASE_URL)

        app = app_builder.build()
        return app
    except (KeyError, TypeError, ValueError) as e:
        logger.error(f"Error creating the Telegram bot application: {e}")
        raise


def add_command_handlers(app):
    """Add command handlers to the bot application."""
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("list", list))
    app.add_handler(CommandHandler("sub", sub))
    app.add_handler(CommandHandler("unsub", unsub))
    app.add_handler(CommandHandler("set", set))
    app.add_handler(MessageHandler(filters.COMMAND, unknown))
    app.add_error_handler(error)


def main():
    try:
        config = load_config()
        app = create_bot_application(config)
        add_command_handlers(app)

        # fixed the restart loading task issue
        # https://docs.python-telegram-bot.org/en/v21.2/telegram.ext.jobqueue.html#telegram.ext.JobQueue.run_once
        app.job_queue.run_once(reload_rss_tasks, 1)

        app.run_polling(poll_interval=3)
        logger.info("Bot is starting...")
    except Exception as e:
        logger.error("Failed to start the bot: %s", e)


if __name__ == '__main__':
    main()
