from unittest import TestCase
from nose import notest

from sodabot import SodaBot

class CommandTest(TestCase):

	def setup():
		self.command = "@sodabot user1:"

	@notest
	def make_test_string(s):
		return "%s %s" % (self.command, s)

	def test_pepsi_purchase(self):
		command = self.make_test_string("pepsi 20 cans of Pepsi Max")

		b =

