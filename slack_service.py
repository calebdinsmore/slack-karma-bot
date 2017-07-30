from slackclient import SlackClient
from models import ApiMessage, ApiUser, ApiChannel, EventKey, EventType
from enum import Enum
from ratelimit import rate_limited
from time import time
import os

class SlackService(object):
    """
        Class that abstracts the Slack client from the rest of the application. 
        Probably should be a Singleton, but whatevs.
    """
    def __init__(self):
        self._client = SlackClient(os.environ.get('KARMA_BOT_TOKEN'))

    def connect(self):
        """
            Connect to Slack's Real Time Messaging service.
        """
        return self._client.rtm_connect()

    def read_stream(self):
        """
            Read from the stream of Slack events. 
            Returns a list of events (could be user connects/disconnects, messages, etc.).
        """
        events = []
        rtm_output_list = self._client.rtm_read()
        for output in rtm_output_list:
            if output[EventKey.TYPE.value] == EventType.MESSAGE.value:
                events.append(ApiMessage(output))
        return events

    def post_message(self, text, channel, as_user=True):
        """
            Posts a message to the desired channel using Slack's postMessage endpoint.
        """
        self._api_call("chat.postMessage", text=text, channel=channel, as_user=as_user)

    def fetch_users(self):
        """
            Gets all the users within a Slack team.
        """
        users = []
        response = self._api_call("users.list")
        if 'members' in response:
            for user in response['members']:
                users.append(ApiUser(user))
        return users

    def get_new_messages(self, oldest_timestamp):
        """
            Fetch messages sent after a given timestamp.
        """
        channels = self.fetch_channels()
        new_messages = []
        for channel in channels:
            messages, has_more = self.fetch_channel_history(channel.id, count=1000, oldest=oldest_timestamp)
            new_messages += messages
            while has_more:
                messages, has_more = self.fetch_channel_history(channel.id, count=1000, 
                        latest=messages[-1].timestamp, oldest=oldest_timestamp)
                new_messages += messages
        return new_messages

    def fetch_all_messages(self):
        """
            This is a monster of a request. 
            This gets all messages in all channels as far back as you can go.
        """
        channels = self.fetch_channels()
        all_messages = []
        for channel in channels:
            messages = self.fetch_channel_history(channel.id, count=1000, latest=time())
            while messages: # while messages is non-empty
                all_messages += messages
                messages = self.fetch_channel_history(channel.id, count=1000, latest=messages[-1].timestamp)
        return all_messages

    def fetch_channels(self):
        """
            Gets all channels within a team.
        """
        channels = []
        response = self._api_call('channels.list')
        if 'channels' in response:
            for channel in response['channels']:
                channels.append(ApiChannel(channel))
        return channels

    def fetch_channel_history(self, channel, count=100, latest=time(), oldest=0):
        messages = []
        response = self._api_call('channels.history', channel=channel, count=count, latest=latest, oldest=oldest)
        if not response['ok']:
            return messages
        if 'messages' in response:
            for message in response['messages']:
                if 'user' in message:
                    messages.append(ApiMessage(message))
        return messages, response['has_more']

    @rate_limited(1) # restricts this function to call once per second, as per Slack's policy
    def _api_call(self, endpoint, **kwargs):
        """
            Executes a call to the Slack API to the desired endpoint.
        """
        return self._client.api_call(endpoint, **kwargs)
