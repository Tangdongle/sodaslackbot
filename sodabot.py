from collections import deque
import os
import re
import json
import time

from datetime import datetime
from slackclient import SlackClient
from config import logger

from commands import *

from models import db, DB_FILE

READ_WEBSOCKET_DELAY = 1

SCANNER = re.compile('[A-Z]{2,}(?![a-z])|[A-Z][a-z]+(?=[A-Z])|[\'\w\-]+''')

BOT_ID = os.environ.get('BOT_ID')

AT_BOT = "sodabot"

slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))

DEFAULT_COMMAND_LIST = {"pepsi": "PepsiCommand"}


class SodaBot(object):
    def __init__(self):
        try:
            db.connect()
        except Exception:
            db.init(DB_FILE)
            db.connect()

        cmd_list_loaded = self.load_command_list()
        if not cmd_list_loaded:
            logger.error("No commands available")

    def load_command_list(self):
        try:
            if os.path.exists(os.path.join(os.curdir, 'cmd.soda')):
                with open('cmd.soda', 'rb') as cmd_fh:
                    self.command_list = json.load(cmd_fh)
            else:
                with open('cmd.soda', 'wb') as cmd_fh:
                    self.command_list = {"pepsi": "PepsiCommand"}
                    json.dump(self.command_list, cmd_fh)
        except IOError as e:
            return False
        except ValueError as je:
            with open('cmd.soda', 'wb') as cmd_fh:
                self.command_list = DEFAULT_COMMAND_LIST
                json.dump(self.command_list, cmd_fh)

        return True

    def parse_slack_output(self, slack_rtm_output):
        if slack_rtm_output not in (None, []):
            for msg in slack_rtm_output:
                content = msg.get('content', None)
                if content is None:
                    return None, None, None
                matches = re.findall(SCANNER, content)
                if matches not in (None, []):
                    user = matches[0]
                    target = matches[1]
                    #Deque for poppality
                    command = deque(matches[2:])

                    if target == AT_BOT:
                        logger.debug("%s has called for the %s command", user, command)
                        return command, msg['channel'], user
        return None, None, None

    def handle_command(self, command, channel,  user):
        if command is None or channel is None:
            return False
        try:
            command_module = self.command_list[command.popleft()]
            #Access our named command
            result = globals()[command_module](command, channel, user)
        except (NameError, KeyError):
            logger.error("%s Error: %s" % (type(e), e.message))
            slack_client.api_call("chat.postMessage", channel=channel, text="@%s I don't understand that command. Available commands are: %s" % (user,
                                                                                                                                                 "\n\t".join(["`{}`".format(com) for com in self.command_list.keys()])), as_user=True)
        except IndexError:
            if str(time.time())[-1] == '4':
                slack_client.api_call("chat.postMessage", channel=channel, text="@%s Hi! I know where you live!" % (user))
            elif str(time.time())[-1] == '7':
                slack_client.api_call("chat.postMessage", channel=channel, text="@%s Hi! I went through your photo albums and now I can memorize the first 8 years of your life!" % (user), as_user=True)
            else:
                slack_client.api_call("chat.postMessage", channel=channel, text="@%s Hi! You didn't supply a command. Wanna just chat about soda?" % (user), as_user=True)

    def loop(self):
        if slack_client.rtm_connect():
            logger.info("SodaBot Running")
            while True:
                command, channel, user = self.parse_slack_output(slack_client.rtm_read())
                if command and channel:
                    self.handle_command(command, channel, user)
                    time.sleep(READ_WEBSOCKET_DELAY)
        else:
            logger.error("%s has called for the %s command", user, command)


if __name__ == '__main__':
    bot = SodaBot()
    bot.loop()


