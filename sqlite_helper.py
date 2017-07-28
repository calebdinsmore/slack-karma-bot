import sqlite3
from models import DbMessage, DbUser

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


if __name__ == '__main__':
    from slack_service import SlackService
    import time
    slack_service = SlackService()
    sqlite_helper = SqliteHelper('karma.db')

    db_users = []
    for api_user in slack_service.fetch_users():
        db_user = DbUser()
        db_user.id = api_user.id
        db_user.karma = 0
        db_user.last_updated = time.time()
        db_user.name = api_user.name
        db_users.append(db_user)
    print(sqlite_helper.add_users(db_users))
