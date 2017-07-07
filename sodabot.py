import os
import time
from slackclient import SlackClient
import re
import logging
import sqlite3

user_target_command = re.compile("^(\w+): @(\w+) (.*)")
pepsi_command_string = "^(\d\d?) cans? of ([\w\s]+). fridge restocked at (\d\d:\d\d\s?[a|p]m)"
pepsi_pattern = re.compile(pepsi_command_string)

logger = logging.getLogger('sodabot')
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('logs/sodabot_debug.log')
fh.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)

logger.addHandler(fh)
logger.addHandler(ch)

BOT_ID = os.environ.get('BOT_ID')

AT_BOT = "sodabot"

slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))

def parse_slack_output(slack_rtm_output):
    if slack_rtm_output not in (None, []):
        for msg in slack_rtm_output:
            content = msg.get('content', None)
            if content is None:
                return None, None, None
            matches = re.match(user_target_command, content)
            if matches is not None:
                user = matches.group(1)
                target = matches.group(2)
                command = matches.group(3)

                if target == AT_BOT:
                    logger.debug("%s has called for the %s command", user, command)
                    return command, msg['channel'], user
    return None, None, None

def handle_command(command, channel, user):
    if command is None or channel is None:
        return False
    pepsi_match = re.match(pepsi_pattern, command.lower())
    if pepsi_match is not None:
        num = pepsi_match.group(1)
        drink_type = pepsi_match.group(2)
        datetime = pepsi_match.group(3)
        slack_client.api_call("chat.postMessage", channel=channel,
                              text="%s bought %s cans of %s on %s" % (user, num, drink_type, datetime), as_user=True)
    else:
        slack_client.api_call("chat.postMessage", channel=channel,
                              text="I don't understand. Pepsi command is '{num} cans of {drink type}. fridge restocked at {HH:MM[a/p]m'", as_user=True)


if __name__ == '__main__':
    READ_WEBSOCKET_DELAY = 1
    if slack_client.rtm_connect():
        print "SodaBot Running"
        while True:
            command, channel, user = parse_slack_output(slack_client.rtm_read())
            if command and channel:
                handle_command(command, channel, user)
            time.sleep(READ_WEBSOCKET_DELAY)
    else:
        print "Connection failed!"


