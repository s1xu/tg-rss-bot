from telegram import Update
from telegram.ext import ContextTypes
from db import Database
from rss import fetch_rss_updates
from telegram.error import BadRequest
import logging

db = Database()
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_name = update.message.from_user.name
    await update.message.reply_text(f"{user_name} 欢迎使用RSS订阅机器人🎉\n\n"
                                    " /list 查看已订阅的RSS链接\n"
                                    " /sub @channelID [url] <mins> 订阅\n"
                                    " /unsub @channelID [url] 取消订阅\n"
                                    " /set @channelID [url] <mins> 设置刷新间隔\n"
                                    )


async def list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    subscriptions = db.get_subscriptions(get_user_id(update, context))
    logger.info(f'subscriptions: {subscriptions}')
    if subscriptions:
        subscription_texts = [
            f"频道: {channel_id}, RSS: {url}, 间隔: {interval}" for url, channel_id, interval in subscriptions]
        # 将列表中的字符串连接起来，每个元素用换行符分隔
        message_text = "\n".join(subscription_texts)
        await update.message.reply_text(message_text)
    else:
        await update.message.reply_text("没有订阅任何RSS链接。")


async def sub_bak(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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


async def sub(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not (2 <= len(context.args) <= 3) or not context.args[0].startswith('@'):
        await update.message.reply_text("使用方法: /sub @频道号 <rss_link> [间隔(mins)]")
        return

    channel_id = context.args[0]
    rss_link = context.args[1]

    try:
        interval = int(context.args[2]) if len(
            context.args) > 2 and context.args[2].strip() else 10
    except ValueError:
        interval = 10

    if not await is_bot_in_channel(update, context, channel_id):
        await update.message.reply_text("请先将我添加到频道中再执行此操作。")
        return

    user_id = get_user_id(update, context)
    if db.subscribe(user_id, rss_link, channel_id, interval):
        # 如果订阅成功，设置RSS刷新任务
        set_rss_task(user_id, rss_link, channel_id, interval, context)
        # 通知用户订阅成功
        await update.message.reply_text(f"成功订阅: {rss_link}, 间隔: {interval} 分钟")
    else:
        # 如果订阅已存在，告知用户
        await update.message.reply_text("订阅失败：您已经订阅了这个RSS。")


async def unsub(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) != 2 or not context.args[0].startswith('@'):
        await update.message.reply_text("使用方法: /unsub @频道号 <rss_link>")
        return

    channel_id = context.args[0]
    rss_link = context.args[1]
    user_id = get_user_id(update, context)
    db.unsubscribe(user_id, rss_link, channel_id)
    task_name = f"{user_id}-{channel_id}" 
    unset_rss_task(task_name, context)
    await update.message.reply_text(f"取消订阅: {rss_link}")


async def set(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) != 3 or not context.args[0].startswith('@'):
        await update.message.reply_text("使用方法: /set @频道号 <rss_link> <间隔(mins)>")
        return

    channel_id = context.args[0]
    rss_link = context.args[1]

    try:
        interval = int(context.args[2]) if len(context.args) > 2 and context.args[2].strip() else 10
    except ValueError:
        interval = 10

    if not await is_bot_in_channel(update, context, channel_id):
        await update.message.reply_text("请先将我添加到频道中再执行此操作。")
        return

    user_id = get_user_id(update, context)
    db.update_interval(user_id, rss_link, channel_id, interval)
    # 取消任务重新设置
    task_name = f"{user_id}-{channel_id}"
    unset_rss_task(task_name, context)
    set_rss_task(user_id, rss_link, channel_id, interval, context)
    # 通知用户订阅成功
    await update.message.reply_text(f"成功设置: {rss_link}, 间隔: {interval} 分钟")


async def fetch_rss_updates_for_subscription(user_id: int, url: str, channel_id: str, context: ContextTypes.DEFAULT_TYPE):
    channel_id = await get_channel_id(context.bot, channel_id)
    if channel_id is None:
        logger.error(f"Failed to get chat ID for {channel_id}")
        return
    updates = fetch_rss_updates(url)
    for update in updates:
        message_id = update['id']
        if not db.is_message_sent(user_id, url, channel_id, message_id):
            message = f"*{update['theme']}*\n[{update['title']}]({update['link']})"
            await context.bot.send_message(chat_id=channel_id, text=message, parse_mode='Markdown')
            db.save_sent_message(user_id, url, channel_id, message_id)


async def fetch_rss_updates_periodically_bak(user_id: int, channel_id: str, context: ContextTypes.DEFAULT_TYPE):
    subscriptions = db.get_subscriptions(user_id)
    for url, channel_id in subscriptions:
        updates = fetch_rss_updates(url)
        for update in updates:
            message_id = update['id']
            if not db.is_message_sent(user_id, url, channel_id, message_id):
                # message = f"标题: {update['title']}\n链接: {update['link']}"
                # message = f"*[{update['title']}]({update['link']})*"
                message = f"*{update['theme']}*\n[{update['title']}]({update['link']})\n"
                await context.bot.send_message(chat_id=channel_id, text=message, parse_mode='Markdown')
                db.save_sent_message(user_id, url, channel_id, message_id)


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


async def reload_rss_tasks(context: ContextTypes.DEFAULT_TYPE):
    subscriptions = db.get_all_subscriptions()
    for subscription in subscriptions:
        user_id = subscription['user_id']
        channel_id = subscription['channel_id']
        rss_link = subscription['rss_link']
        interval = subscription['interval']
        # 重新设置定时任务
        channel_id = await get_channel_id(context.bot, channel_id)
        logger.info(
            f"Reloading task for {user_id}, {rss_link}, {channel_id}, {interval} success.")
        if channel_id is None:
            logging.error(
                f"Failed to get channel ID for {channel_id}, skipping task setup.")
            continue

        set_rss_task(user_id, rss_link, channel_id, interval, context)


# def set_rss_task_bak(user_id: int, channel_id: str, rss_link: str, interval: int, context: ContextTypes.DEFAULT_TYPE) -> None:
#     async def task_callback(context):
#         await fetch_rss_updates_periodically(user_id, channel_id, context)

#     context.job_queue.run_repeating(task_callback, interval=interval * 60, name=str(user_id))

def set_rss_task(user_id: int, url: str, channel_id: str, interval: int, context: ContextTypes.DEFAULT_TYPE):
    async def task_callback(context):
        await fetch_rss_updates_for_subscription(user_id, url, channel_id, context)
    
    # fixed an issue where push stops after a period of time
    # https://github.com/python-telegram-bot/python-telegram-bot/issues/3424#issuecomment-1353290602
    job = context.job_queue.run_repeating(
        task_callback, interval=interval * 60, name=f"{user_id}-{channel_id}")
    logger.info("Added job: %s", job.name)


def unset_rss_task(name: str, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info(f"Removing job {name}")
    current_job = context.job_queue.get_jobs_by_name(name)
    if not current_job:
        False
    for job in current_job:
        job.schedule_removal()
    return True


def get_user_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info(f'update.message: {update.message}')
    return update.message.from_user.id


async def get_channel_id(bot, channel_username):
    try:
        chat = await bot.get_chat(channel_username)
        return chat.id
    except Exception as e:
        logger.warn(f"Failed to get chat ID for {channel_username}: {e}")
        return None


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("我暂时还不会这个哦~")


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.error(f'Update {update} caused error {context.error}')
