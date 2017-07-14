from unittest import TestCase
from nose.tools import nottest

from commands import PepsiCommand
from models import User

class PepsiCommandTest(TestCase):

	def test_pepsi_purchase(self):
		command = "pepsi 20 cans of Pepsi Max"

		command_list = command.split(" ")

		channel = 'BotTest'

		user = User(username="user1")

		b = PepsiCommand(command_list, channel, user)

