# pylint: disable=C0103
from enum import Enum

class EventKey(Enum):
    TYPE = 'type'
    CHANNEL = 'channel'
    USER = 'user'
    TEXT = 'text'
    TIMESTAMP = 'ts'
    REACTIONS = 'reactions'

class EventType(Enum):
    MESSAGE = 'message'
    ERROR = 'error'

"""
    API Models
"""
class Event(object):
    def __init__(self, rtm_event):
        self.type = rtm_event[EventKey.TYPE]

class ApiMessage(Event):
    def __init__(self, rtm_event):
        Event.__init__(self, rtm_event)
        self.channel = rtm_event[EventKey.CHANNEL]
        self.user = rtm_event[EventKey.USER]
        self.text = rtm_event[EventKey.TEXT]
        self.text_split = self.text.split()
        self.timestamp = rtm_event[EventKey.TIMESTAMP]
        self.reactions = []
        if rtm_event['reactions']: # contains upvote/downvote information -- important!
            self.reactions = rtm_event['reactions']

class ApiUser(object):
    """
        Represents a User received from the Slack API.
        Only has an id attribute, since that's all I care about.
    """
    def __init__(self, api_object):
        self.id = api_object['id']
        self.name = api_object['name']

class ApiChannel(object):
    """
        Represents a Channel received from the Slack API.
        Only has an id attribute, since that's all I care about.
    """
    def __init__(self, api_object):
        self.id = api_object['id']

"""
    DB Models
"""
class DbUser(object):
    def __init__(self, user_row=None):
        if user_row:
            self.id = user_row[0]
            self.name = user_row[1]
            self.karma = user_row[2]
            self.last_updated = user_row[3]

    def to_row(self):
        """
            Returns db row representation of itself.
        """
        return (self.id, self.name, self.karma, self.last_updated)

class DbMessage(object):
    def __init__(self, message_row=None):
        if message_row:
            self.id = message_row[0]
            self.text = message_row[1]
            self.upvotes = message_row[2]
            self.downvotes = message_row[3]
            self.timestamp = message_row[4]
            self.user_id = message_row[5]

    def to_row(self):
        """
            Returns db row representation of itself.
        """
        return (self.id, self.text, self.upvotes, self.downvotes,
                self.timestamp, self.user_id)
