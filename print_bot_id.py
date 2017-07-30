import os
from slackclient import SlackClient

BOT_NAME = "edukarma"

slackclient = SlackClient(os.environ.get('KARMA_BOT_TOKEN'))

if __name__ == "__main__":
    api_call = slackclient.api_call("users.list")
    if api_call.get('ok'):
        users = api_call.get('members')
        for user in users:
            if 'name' in user and user.get('name') == BOT_NAME:
                print("Bot ID for '" + user['name'] + "' is " + user['id'])
    else:
        print("Could not find user with the name " + BOT_NAME)