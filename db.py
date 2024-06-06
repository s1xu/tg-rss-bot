import sqlite3


class Database:
    def __init__(self, db_name='rss_subs.db'):
        self.conn = sqlite3.connect(db_name)
        self.init_db()

    def init_db(self):
        c = self.conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS subscriptions (
                     id INTEGER PRIMARY KEY AUTOINCREMENT, 
                     url TEXT,
                     channel_id TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS sent_messages (
                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                     url TEXT,
                     channel_id TEXT,
                     message_id TEXT)''')
        self.conn.commit()

    def subscribe(self, url, channel_id):
        c = self.conn.cursor()
        c.execute(
            "INSERT INTO subscriptions (url, channel_id) VALUES (?, ?)", (url, channel_id))
        self.conn.commit()

    def unsubscribe(self, url, channel_id):
        c = self.conn.cursor()
        c.execute(
            "DELETE FROM subscriptions WHERE url = ? AND channel_id = ?", (url, channel_id))
        self.conn.commit()

    def get_subscriptions(self):
        c = self.conn.cursor()
        c.execute("SELECT url, channel_id FROM subscriptions")
        rows = c.fetchall()
        return rows

    def save_sent_message(self, url, channel_id, message_id):
        c = self.conn.cursor()
        c.execute("INSERT INTO sent_messages (url, channel_id, message_id) VALUES (?, ?, ?)",
                  (url, channel_id, message_id))
        self.conn.commit()

    def is_message_sent(self, url, channel_id, message_id):
        c = self.conn.cursor()
        c.execute("SELECT id FROM sent_messages WHERE url = ? AND channel_id = ? AND message_id = ?",
                  (url, channel_id, message_id))
        row = c.fetchone()
        return row is not None

    def close(self):
        self.conn.close()
