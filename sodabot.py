import os
import time
from slackclient import SlackClient
import re
import logging
from peewee import IntegrityError as ieerror
from peewee import *
from datetime import datetime

DB_FILE = 'db/sodarecords.db'

db = SqliteDatabase(DB_FILE)

user_target_command = re.compile("^(\w+): @(\w+) (.*)")
pepsi_command_string = "^(\d\d?) cans? of ([\w\s]+).*"
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


class User(Model):
    username = CharField(unique=True, primary_key=True)

    class Meta:
        database = db

class DrinkType(Model):
    name = CharField(unique=True, primary_key=True)

    class Meta:
        database = db

class Purchase(Model):
    buyer = ForeignKeyField(User, related_name='purchases')
    drink_type = ForeignKeyField(DrinkType, related_name='drink_types')
    num_cans = IntegerField()
    purchase_date = DateTimeField()

    class Meta:
        database = db

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

def handle_command(command, channel,  user):
    if command is None or channel is None:
        return False
    pepsi_match = re.match(pepsi_pattern, command.lower())
    if pepsi_match is not None:
        num = pepsi_match.group(1)
        drink_type = pepsi_match.group(2)
        dt = datetime.utcnow()

        user_model = get_user(user)
        drink_model = get_drink_type(drink_type)
        purchase = add_purchase(
            buyer=user_model,
            drink_type=drink_model,
            purchase_date=dt,
            num_cans=num
        )
        if purchase:
            slack_client.api_call("chat.postMessage", channel=channel,

                                  text="%s bought %s cans of %s on %s" % (user, num, drink_type, dt.strftime("%A, %m-%d %H:%M")), as_user=True)
        else:
            slack_client.api_call("chat.postMessage", channel=channel,

                                text="Purchase failed!")

    else:
        slack_client.api_call("chat.postMessage", channel=channel,
                              text="I don't understand. Pepsi command is '{num} cans of {drink type}'", as_user=True)

def get_user(username):
    try:
        with db.atomic():
            return User.create(username=username)
    except ieerror:
        return User.get(User.username == username)

def get_drink_type(drink_type):
    try:
        with db.atomic():
            return DrinkType.create(name=drink_type)
    except ieerror:
        return DrinkType.get(DrinkType.name == drink_type)

def add_purchase(buyer, drink_type, purchase_date, num_cans):
    try:
        with db.atomic():
            return Purchase.create(buyer=buyer, drink_type=drink_type, purchase_date=purchase_date, num_cans=num_cans)
    except ieerror as ie:
        logger.debug("Error: %s", ie.message)
        return None


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


