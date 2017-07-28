from slack_service import SlackService
from models import EventType
from enum import Enum
import os
import time

BOT_ID = os.environ.get('KARMA_BOT_ID')
AT_BOT = "<@" + BOT_ID + ">"

class Commands(Enum):
    SHOW = 'show'
    GIVE = 'give'

class BotCommand(object):
    def __init__(self, message, bot_mention=None):
        self.channel = message.channel
        self.user = message.user
        self.text = ' '.join(message.text.split()).lower() # remove extra whitespace and lower
        if bot_mention:
            self.text = ''.join(self.text.split(bot_mention)).lower()
        self.text_split = self.text.split()

class KarmaBot(object):
    def __init__(self, api, bot_id, bot_mention):
        self.api = api
        self.bot_id = bot_id
        self.bot_mention = bot_mention

    def process_events(self, events):
        for event in events:
            if event.type == EventType.MESSAGE:
                if self.bot_mention in event.text:
                    self.handle_command(BotCommand(event))

    def handle_command(self, command):
        """
            Receives commands directed at the bot and determines if they
            are valid commands. If so, then acts on the commands. If not,
            returns back what it needs for clarification.
        """
        response = "Not sure what you mean. Use the *" + Commands.SHOW + \
                "* command with numbers, delimited by spaces."
        if Commands.SHOW in command.text_split:
            response = self._show_command(command)
        self.api.post_message(response, channel=command.channel)

    def _show_command(self, command):
        if command.text_split[1].lower() == 'my' and command.text_split[2].lower() == 'karma':
            self._get_karma(command)

    def _get_karma(self, command):
        """
            Retrieves the karma for the requested user.
        """
        pass


if __name__ == '__main__':
    slack_service = SlackService()
    karma_bot = KarmaBot(slack_service, BOT_ID, AT_BOT)
    READ_WEBSOCKET_DELAY = 1 # one second read delay
    if slack_service.connect():
        print("Karma Bot up and running!")
        while True:
            events = slack_service.read_stream()
            if len(events) > 0:
                karma_bot.process_events(events)
            time.sleep(READ_WEBSOCKET_DELAY)
