import sqlite3

class BotDB:
    def __init__(self, db_file: str) -> None:
        self.conn = sqlite3.connect(db_file)
        self.cursor = self.conn.cursor()

    def userExists(self, user_id: int) -> bool:
        result = self.cursor.execute("SELECT id FROM users WHERE user_id = ?", (user_id,))
        return bool(len(result.fetchall()))

    def addUser(self, user_id: int, user_first_name: str, group_id: int, chat_id: int) -> None:
        self.cursor.execute("INSERT INTO users (user_id, user_first_name, group_id, chat_id) VALUES(?, ?, ?, ?)", (user_id, user_first_name, group_id, chat_id,))
        self.conn.commit()

    def getGroups(self) -> list:
        return self.cursor.execute("SELECT * FROM groups").fetchall()
    def getEventsInGroup(self, group_id: int) -> list:
        return self.cursor.execute("SELECT * FROM events WHERE group_id = ?", (group_id,)).fetchall()
    def getUsersInGroup(self, group_id: int) -> list:
        return self.cursor.execute("SELECT * FROM users WHERE group_id = ?", (group_id,)).fetchall()
    def getUserById(self, user_id: int) -> list:
        return self.cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchall()

    def getVideos(self) -> list:
        return self.cursor.execute("SELECT * FROM videos").fetchall()
    def getLinks(self) -> list:
        return self.cursor.execute("SELECT * FROM links").fetchall()

    def close(self) -> None:
        self.conn.close()