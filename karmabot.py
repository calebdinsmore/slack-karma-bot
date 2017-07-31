from __future__ import division
from slack_service import SlackService
from sqlite_helper import SqliteHelper
from models import EventType, DbMessage
from enum import Enum
import os
import time
import traceback

BOT_ID = os.environ.get('KARMA_BOT_ID')
AT_BOT = "<@" + BOT_ID + ">"

class Commands(Enum):
    SHOW = 'show'
    GIVE = 'give'
    INTRO = 'introduce'
    HELP = 'help'
    UPDATE = 'update'
    FORCE = 'force'

class BotCommand(object):
    def __init__(self, message, bot_mention=None):
        self.channel = message.channel
        self.user = message.user
        self.text = ' '.join(message.text.split()).lower() # remove extra whitespace and lower
        if bot_mention:
            self.text = ''.join(self.text.split(bot_mention)).lower()
        self.text_split = self.text.split()

class KarmaBot(object):
    def __init__(self, api, sql_helper, bot_id, bot_mention):
        self.api = api
        self.sql_helper = sql_helper
        self.bot_id = bot_id
        self.bot_mention = bot_mention

    def process_events(self, events):
        for event in events:
            if event.type == EventType.MESSAGE.value:
                if event.text and self.bot_mention in event.text:
                    self.handle_command(BotCommand(event))

    def handle_command(self, command):
        """
            Receives commands directed at the bot and determines if they
            are valid commands. If so, then acts on the commands. If not,
            returns back what it needs for clarification.
        """
        response =  "I'm sorry; I don't quite understand. " + self._help_message()
        print(command.user, command.text)
        if Commands.SHOW.value in command.text_split:
            response = self._show_command(command)
        elif Commands.HELP.value in command.text_split:
            response = self._help_message()
        elif Commands.INTRO.value in command.text_split:
            response = self._introduction_message()
        elif Commands.UPDATE.value in command.text_split:
            if command.user != 'U0T66D1D5':
                response = "I'm sorry; only my creator can tell me to do that."
                return
            if Commands.FORCE.value not in command.text_split:
                response = "Do you want me to update my database of Slack messages? This can " + \
                        "take a little while to do, but if you're sure, tell me " + \
                         "`@edukarma force update`."
            else:
                self.api.post_message('Excuse me for a moment while I update my database of Slack messages.', 
                        channel=command.channel)
                self._update_messages(notify_completion=True, channel=command.channel)
                return
        self.api.post_message(response, channel=command.channel)

    def _show_command(self, command):
        if 'my' in command.text_split and 'karma' in command.text_split:
            return self._get_karma(command)

    def _get_karma(self, command):
        """
            Retrieves the karma for the requested user.
        """
        # if it's been more than a day since last update
        latest_message_time = self.sql_helper.get_latest_message_timestamp()
        if not latest_message_time:
            return 'Had an error in my system. Sorry! Better luck next time.'
        if time.time() - latest_message_time > 86400:
            self.api.post_message('Excuse me for a moment while I update my database of Slack messages.', command.channel)
            self._update_messages()
        upvotes, downvotes = self.sql_helper.get_votes_for_user(command.user)
        response = 'According to my calculations, <@' + command.user + '>\'s karma is *%d* (%d upvotes, %d downvotes).' % \
                (upvotes - downvotes, upvotes, downvotes)
        if upvotes + downvotes > 0:
            response += ' Your messages are %.2f%% upvoted.' % (upvotes / (upvotes + downvotes) * 100)
        return response

    def _update_messages(self, notify_completion=False, channel=None):
        db_messages_to_add = []
        most_recent_timestamp = self.sql_helper.get_latest_message_timestamp()
        new_messages = self.api.get_new_messages(most_recent_timestamp)
        for api_message in new_messages:
            db_message = DbMessage()
            db_message.init_from_api_message(api_message)
            db_messages_to_add.append(db_message)
        self.sql_helper.add_messages(db_messages_to_add)
        if notify_completion:
            self.api.post_message('Done updating!', channel)

    def _help_message(self):
        help_string = "Try asking me these things:\n"
        help_string += "`@edukarma show me my karma`\n"
        help_string += "`@edukarma help (shows this message)`\n"
        help_string += "`@edukarma update`\n"
        help_string += "If you want to talk to me privately, send me a direct message!"
        return help_string

    def _introduction_message(self):
        intro_string = "*Hello!* I'm EduKarma, your friendly Slack karma calculator.\n"
        intro_string += "I'll _probably_ do/say more things in the future, but for now, try asking this:\n"
        intro_string += "`@edukarma show me my karma`\n"
        intro_string += "If you want to check your karma privately, send me a direct message!"
        return intro_string

if __name__ == '__main__':
    slack_service = SlackService()
    karma_bot = KarmaBot(slack_service, SqliteHelper('karma.db'), BOT_ID, AT_BOT)
    READ_WEBSOCKET_DELAY = 1 # one second read delay
    try:
        if slack_service.connect():
            print("Karma Bot up and running!")
            while True:
                events = slack_service.read_stream()
                if events:
                    karma_bot.process_events(events)
                time.sleep(READ_WEBSOCKET_DELAY)
    except Exception:
        slack_service.post_message('Something went wrong! Please restart me, <@U0T66D1D5>.\n' + \
        traceback.format_exc(), 'C6F9UP2NB')
