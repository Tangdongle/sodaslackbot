from collections import deque
import os
import re
import time

from datetime import datetime
from peewee import IntegrityError as ieerror
from slackclient import SlackClient
from config import logger

from commands import *

from models import db

READ_WEBSOCKET_DELAY = 1

SCANNER = re.compile('[A-Z]{2,}(?![a-z])|[A-Z][a-z]+(?=[A-Z])|[\'\w\-]+''')
COMMAND_LIST = {
    "pepsi": Pepsi
}

#Matches the user sending (1), the target user (2) and the command (3)
#user_target_command = re.compile("^(\w+): @(\w+) (.*)")
#pepsi_command_string = "^(\d\d?) cans? of ([\w\s]+).*"
#
#add_for_user_command_string = "^(\w+)! (\d\d?) cans? of ([\w\s]+).*"

#pepsi_pattern = re.compile(pepsi_command_string)


BOT_ID = os.environ.get('BOT_ID')

AT_BOT = "sodabot"

slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))



class SodaBot(object):
	def __init__(self):
		pass

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
			print command
			#Access our named command
			result = COMMAND_LIST[command.popleft()](command, channel, user)
		except (NameError, KeyError):
			slack_client.api_call("chat.postMessage", channel=channel, text="@%s I don't understand that command. Available commands are: %s" % (user.username, "\n\t".join(["`{}`".format(com) for com in COMMAND_LIST.keys()])), as_user=True)
		except IndexError:
			if str(time.time())[-1] == '4':
				slack_client.api_call("chat.postMessage", channel=channel, text="@%s Hi! I know where you live!" % (user.username))
			if str(time.time())[-1] == '7':
				slack_client.api_call("chat.postMessage", channel=channel, text="@%s Hi! I went through your photo albums and now I can memorize the first 8 years of your life!" % (user.username), as_user=True)
			else:
				slack_client.api_call("chat.postMessage", channel=channel, text="@%s Hi! You didn't supply a command. Wanna just chat about soda?" % (user.username), as_user=True)

	def loop(self):
		if slack_client.rtm_connect():
			print "SodaBot Running"
			while True:
				command, channel, user = bot.parse_slack_output(slack_client.rtm_read())
				if command and channel:
					bot.handle_command(command, channel, user)
				time.sleep(READ_WEBSOCKET_DELAY)
		else:
			print "Connection failed!"


if __name__ == '__main__':
	bot = SodaBot()
	bot.loop()


