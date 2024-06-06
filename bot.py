from telegram import Update
from telegram.ext import ContextTypes
from db import Database
from rss import fetch_rss_updates
from telegram.error import BadRequest

db = Database()


async def list_subscriptions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    subscriptions = db.get_subscriptions()
    if subscriptions:
        subscription_texts = [
            f"频道: {channel_id}, RSS链接: {url}" for url, channel_id in subscriptions]
        message_text = "\n".join(subscription_texts)
        await update.message.reply_text(message_text)
    else:
        await update.message.reply_text("没有订阅任何RSS链接。")


async def sub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2 or not context.args[0].startswith('@'):
        await update.message.reply_text("使用方法: /sub @频道号 <rss_link>")
        return

    channel_id = context.args[0]
    rss_link = context.args[1]
    if not await is_bot_in_channel(update, context, channel_id):
        await update.message.reply_text("请先将我添加到频道中再执行此操作。")
        return
    db.subscribe(rss_link, channel_id)
    await update.message.reply_text(f"成功订阅: {rss_link}")


async def unsub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2 or not context.args[0].startswith('@'):
        await update.message.reply_text("使用方法: /unsub @频道号 <rss_link>")
        return

    channel_id = context.args[0]
    rss_link = context.args[1]
    db.unsubscribe(rss_link, channel_id)
    await update.message.reply_text(f"取消订阅: {rss_link}")


async def fetch_rss_updates_periodically(context: ContextTypes.DEFAULT_TYPE):
    subscriptions = db.get_subscriptions()
    for url, channel_id in subscriptions:
        updates = fetch_rss_updates(url)
        for update in updates:
            message_id = update['id']
            if not db.is_message_sent(url, channel_id, message_id):
                # message = f"标题: {update['title']}\n链接: {update['link']}"
                # message = f"*[{update['title']}]({update['link']})*"
                message = f"*{update['theme']}*\n[{update['title']}]({update['link']})\n"
                await context.bot.send_message(chat_id=channel_id, text=message, parse_mode='Markdown')
                db.save_sent_message(url, channel_id, message_id)


async def is_bot_in_channel(update: Update, context: ContextTypes.DEFAULT_TYPE, channel_id: str) -> bool:
    bot = await context.bot.get_me()
    try:
        member = await context.bot.get_chat_member(channel_id, bot.id)
        if member.status == 'administrator':
            # 可以进一步检查具体权限，例如 can_post_messages, can_edit_messages 等
            return True
    except BadRequest:
        pass
    return False
