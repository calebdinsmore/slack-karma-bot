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
        print(os.environ.get('KARMA_BOT_TOKEN'))
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
            if output[EventKey.TYPE] == EventType.MESSAGE:
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

    def fetch_all_messages(self):
        """
            This is a monster of a request. 
            This gets all messages in all channels as far back as you can go.
        """
        channels = self.fetch_channels()
        all_messages = []
        for channel in channels:
            messages = self.fetch_channel_history(channel.id, count=1000)
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
        if response['channels']:
            for channel in response['channels']:
                channels.append(ApiChannel(channel))
        return channels

    def fetch_channel_history(self, channel, count=100, latest=time()):
        messages = []
        response = self._api_call('channels.history', channel=channel, count=count, latest=latest)
        if response['messages']:
            for message in response['messages']:
                messages.append(ApiMessage(message))

    @rate_limited(1) # restricts this function to call once per second, as per Slack's policy
    def _api_call(self, endpoint, **kwargs):
        """
            Executes a call to the Slack API to the desired endpoint.
        """
        return self._client.api_call(endpoint, **kwargs)
