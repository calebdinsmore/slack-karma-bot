import sqlite3
from models import DbMessage, DbUser, ReactionNames

class SqliteHelper(object):
    """
        This class manages interfacing with the SQLite database. It stores DbUser and DbMessage
        objects (see: models.py).
    """
    def __init__(self, db_file):
        self.connection = sqlite3.connect(db_file)
        self.cursor = self.connection.cursor()

    def get_messages_for_user(self, user_id):
        """
            Fetches all messages in the database for a given user.
            Returns an array of DbMessage objects (models.py)
        """
        messages = []
        args = (user_id,)
        query = "SELECT * FROM Message WHERE user_id=?"
        rows = self._execute_query(query, args)
        
        for row in rows:
            messages.append(DbMessage(row))
        return messages

    def add_users(self, users):
        """
            Adds users to the database.
        """
        query = 'INSERT INTO User VALUES (?, ?, ?, ?)'
        users_as_rows = []
        for user in users:
            users_as_rows.append(user.to_row())
        return self._execute_many_query(query, users_as_rows)

    def add_messages(self, messages):
        """
            Adds messages to the database.
        """
        query = 'INSERT INTO Message VALUES (?, ?, ?, ?, ?)'
        messages_as_rows = []
        for db_message in messages:
            messages_as_rows.append(db_message.to_row())
        return self._execute_many_query(query, messages_as_rows)

    def _execute_query(self, query, args=None):
        """
            Protected method that executes a database query.
            `args` represents arguments for the WHERE clause, like user_id and such.
        """
        if args:
            self.cursor.execute(query, args)
        else:
            self.cursor.execute(query)
        return self.cursor.fetchall()

    def _execute_many_query(self, query, args):
        with self.connection:
            self.cursor.executemany(query, args)
        return self.cursor.fetchall()
