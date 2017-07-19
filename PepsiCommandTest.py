from unittest import TestCase
from nose.tools import nottest

import commands
from models import User

class PepsiCommandTest(TestCase):

	def test_pepsi_default(self):
		command = "20 cans of Pepsi Max"

		command_list = command.split(" ")

		channel = 'BotTest'

		user = User(username="user1")

		b = commands.PepsiCommand(command_list, channel, user)

