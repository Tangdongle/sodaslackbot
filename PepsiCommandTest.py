from unittest import TestCase
from nose.tools import nottest
from peewee import *
from config import logger
from slackclient import SlackClient

import commands
from models import User, db, DrinkType, Purchase

class PepsiCommandTest(TestCase):

    def setUp(self):
        db.init(':memory:')
        db.connect()
        db.create_tables([User, DrinkType, Purchase])

    def test_pepsi_default(self):
        command = "20 cans of Pepsi Max"

        command_list = command.split(" ")

        channel = 'bottystuff'

        user = User(username="user1")

        b = commands.PepsiCommand(command_list, channel, user)

        for u in User.select():
            print u.username

        u = User.get(User.username == 'user1')
        self.assertTrue(u)

        for d in DrinkType.select():
            print d.name
        dt = DrinkType.get(DrinkType.name == 'Pepsi Max')

        self.assertTrue(dt)

        user2 = User(username="user2")

        command = "50 cans of Big Ol' Beer"

        command_list = command.split(" ")

        b = commands.PepsiCommand(command_list, channel, user2)

    def test_list(self):
        command = ["list"]

        channel = 'bottystuff'

        user = User(username="user1")

        b = commands.PepsiCommand(command, channel, user)

        for p in Purchase.select():
            logger.warn(p.buyer)
            logger.warn(p.drink_type)



