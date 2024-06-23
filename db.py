import sqlite3


class Database:
    def __init__(self, db_name="rss_subs.db"):
        self.conn = sqlite3.connect(db_name)
        self.init_db()

    def init_db(self):
        c = self.conn.cursor()
        c.execute("""
                  CREATE TABLE IF NOT EXISTS subscriptions (
                     id INTEGER PRIMARY KEY AUTOINCREMENT, 
                     user_id INTEGER,
                     url TEXT,
                     channel_id TEXT,
                     interval INTEGER DEFAULT 10
                  )
                  """)
        c.execute("""
                  CREATE TABLE IF NOT EXISTS sent_messages (
                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                     user_id INTEGER,
                     url TEXT,
                     channel_id TEXT,
                     message_id TEXT
                  )
                  """)
        self.conn.commit()

    def subscribe(self, user_id, url, channel_id, interval):
        c = self.conn.cursor()
        try:
            c.execute(
                "SELECT * FROM subscriptions WHERE user_id = ? AND url = ? AND channel_id = ?",
                (user_id, url, channel_id),
            )
            if c.fetchone():
                return False
            else:
                c.execute(
                    "INSERT INTO subscriptions (user_id, url, channel_id, interval) VALUES (?, ?, ?, ?)",
                    (user_id, url, channel_id, interval),
                )
                self.conn.commit()
                return True
        finally:
            c.close()

    def unsubscribe(self, user_id, url, channel_id):
        c = self.conn.cursor()
        try:
            c.execute(
                "DELETE FROM subscriptions WHERE user_id = ? AND url = ? AND channel_id = ?",
                (user_id, url, channel_id),
            )
            self.conn.commit()
        finally:
            c.close()

    def update_interval(self, user_id, url, channel_id, interval):
        c = self.conn.cursor()
        try:
            c.execute(
                "UPDATE subscriptions SET interval = ? WHERE user_id = ? AND url = ? AND channel_id = ?",
                (interval, user_id, url, channel_id),
            )
            self.conn.commit()
        finally:
            c.close()

    def get_subscriptions(self, user_id):
        c = self.conn.cursor()
        try:
            c.execute(
                "SELECT url, channel_id, interval FROM subscriptions WHERE user_id = ?",
                (user_id,),
            )
            rows = c.fetchall()
            return rows
        finally:
            c.close()

    def get_all_subscriptions(self):
        c = self.conn.cursor()
        c.execute("SELECT user_id, url, channel_id, interval FROM subscriptions")
        subscriptions = [
            {
                "user_id": row[0],
                "rss_link": row[1],
                "channel_id": row[2],
                "interval": row[3],
            }
            for row in c.fetchall()
        ]
        c.close()
        return subscriptions

    def save_sent_message(self, user_id, url, channel_id, message_id):
        c = self.conn.cursor()
        try:
            c.execute(
                "INSERT INTO sent_messages (user_id, url, channel_id, message_id) VALUES (?, ?, ?, ?)",
                (user_id, url, channel_id, message_id),
            )
            self.conn.commit()
        finally:
            c.close()

    def is_message_sent(self, user_id, url, channel_id, message_id):
        c = self.conn.cursor()
        try:
            c.execute(
                "SELECT id FROM sent_messages WHERE user_id = ? AND url = ? AND channel_id = ? AND message_id = ?",
                (user_id, url, channel_id, message_id),
            )
            row = c.fetchone()
            return row is not None
        finally:
            c.close()

    def close(self):
        self.conn.close()
