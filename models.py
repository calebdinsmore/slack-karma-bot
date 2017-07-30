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

class ReactionNames(Enum):
    UPVOTE = 'upvote'
    DOWNVOTE = 'downvote'

"""
    API Models
"""
class Event(object):
    def __init__(self, rtm_event):
        self.type = rtm_event[EventKey.TYPE.value]

class ApiMessage(Event):
    def __init__(self, rtm_event):
        Event.__init__(self, rtm_event)
        self.user = rtm_event[EventKey.USER.value]
        self.channel = rtm_event[EventKey.CHANNEL.value] if EventKey.CHANNEL.value in rtm_event else None
        self.text = rtm_event[EventKey.TEXT.value]
        self.text_split = self.text.split()
        self.timestamp = rtm_event[EventKey.TIMESTAMP.value]
        self.reactions = []
        if EventKey.REACTIONS.value in rtm_event: # contains upvote/downvote information -- important!
            for json_reaction in rtm_event[EventKey.REACTIONS.value]:
                self.reactions.append(ApiReaction(json_reaction))

    def get_reaction_count(self, name):
        """
            Gets the count associated with a given reaction for this message.
            For the purposes of this bot, this will really only be used for
            upvotes and downvotes.
        """
        if self.reactions:
            for reaction in self.reactions:
                if reaction.name == name:
                    return reaction.count
        return 0

class ApiReaction(object):
    def __init__(self, reaction_object):
        self.name = reaction_object['name']
        self.count = reaction_object['count']

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
            self.slack_id = user_row[0]
            self.name = user_row[1]
            self.karma = user_row[2]
            self.last_updated = user_row[3]

    def to_row(self):
        """
            Returns db row representation of itself.
        """
        return (self.slack_id, self.name, self.karma, self.last_updated)

class DbMessage(object):
    def __init__(self, message_row=None):
        if message_row:
            self.text = message_row[1]
            self.upvotes = message_row[2]
            self.downvotes = message_row[3]
            self.timestamp = message_row[4]
            self.user_id = message_row[5]

    def init_from_api_message(self, api_message):
        """
            Set attributes from an ApiMessage object
        """
        self.text = api_message.text
        self.upvotes = api_message.get_reaction_count(ReactionNames.UPVOTE.value)
        self.downvotes = api_message.get_reaction_count(ReactionNames.DOWNVOTE.value)
        self.timestamp = api_message.timestamp
        self.user_id = api_message.user

    def to_row(self):
        """
            Returns db row representation of itself.
        """
        return (self.text, self.upvotes, self.downvotes,
                self.timestamp, self.user_id)
