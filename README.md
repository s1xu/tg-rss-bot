# TG-RSS-BOT

这是一个Python编写的机器人，用于定时检查RSS更新并推送到tg。

## 功能

- `/start`：启动机器人。
- `/list`：列出当前所有订阅的RSS源。
- `/sub`：@channelid `[url]` <mins> 订阅新的RSS源。
- `/unsub`：@channelid `[url]` 取消订阅。
- `/set`: @channelid `[url]` <mins> 设置抓取间隔。
- 自动抓取和推送RSS更新。

## 环境配置

项目依赖于以下主要组件：

- Python 3.8 或更高版本
- python-telegram-bot 21.2 或更高版本
- PyYAML 用于解析配置文件

## 安装

首先，克隆仓库到本地：

```bash
git clone https://github.com/s1xu/tg-rss-bot.git
cd tg-rss-bot
```

安装所需的依赖：

```bash
pip install -r requirements.txt
```

## 配置

修改 `config.yml` 的文件

```yaml
bot_token: "your_telegram_bot_token_here"
endpoint: "https://xxx.com/bot"<optional custom telegram api endpoint>
```

## 运行

执行下面的命令来启动机器人：

```bash
python main.py
```
