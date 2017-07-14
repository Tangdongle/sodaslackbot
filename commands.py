from functools import wraps
from collections import deque
from copy import copy
import re

from models import User, Purchase, DrinkType
from config import logger

REGISTRY = {}

class register_command(object):
    def __init__(cls, command):
        cls._registered_command = command

    def __call__(cls, *args, **kwargs):
        return cls._registered_command(*args, **kwargs)

class default_command(object):
    def __init__(cls, command):
        cls._default_command = command

    def __call__(cls, *args, **kwargs):
        return cls._default_command(*args, **kwargs)

class pattern_must_match(object):
    def __init__(self, pattern):
        self._pattern = re.compile(pattern)
        print "init"

    def syntax_error(self, message, fn, *args, **kwargs):
        logger.debug("Syntax Error: %s : %s in %s: %s", message, self.__class__, fn.__name__, message)

    def __call__(self, fn, *args, **kwargs):
        print "called"

        def ret_fun(*args, **kwargs):
            print self
            print args
            if re.match(self._pattern, " ".join(args)) is not None:
                return fn(self, *args, **kwargs)
            else:
                return self.syntax_error("pattern_must_match error: ", fn, *args, **kwargs)
        return ret_fun

class MetaClass(type):
    def __init__(cls, name, bases, attrs):
        if cls._module_id not in (None, ""):
            module_id = cls._module_id.lower()

            REGISTRY[module_id] = {}
            for key, val in attrs.iteritems():
                registered_command = getattr(val, '_registered_command', None)
                if registered_command is not None:
                    REGISTRY[module_id][key] = registered_command

                default_command = getattr(val, '_default_command', None)
                if default_command is not None:
                    #If we have more than one default, we bail out
                    if REGISTRY[module_id].get('default', None):
                        raise Exception("Cannot have more than 1 default command")
                    REGISTRY[module_id]['default'] = default_command
        else:
            #We skip any class without a _module_id
            print "Skipping %s" % cls.__class__

class BotCommandModule(object):
    __metaclass__ = MetaClass
    _module_id = ""


    def command_error(self, message, command, *args, **kwrgs):
        logger.debug("Unknown command with command %s and args %s: %s", command, args, message)

class PepsiCommand(BotCommandModule):

    _module_id = "Pepsi"

    @register_command
    def me(self, args):
        pass

    @register_command
    def list(self, args):
        print "TEST"

    @default_command
    @register_command
    @pattern_must_match('(\d\d?) cans? of ([\w\s]+).*')
    def purchase(self, args):
        print args
        return args

    def __init__(self, command, channel, user):
        if not isinstance(command, deque):
            command = deque(command)

        module_id = self._module_id.lower()

        command_name = command.popleft()
        if command_name == module_id:
            command_name = 'default'

        self._registry = REGISTRY[module_id]
        print self._registry

        try:
            self._registry[command_name]()
        except KeyError as ie:
            self.command_error(ie.message, command_name, command)



    #    num = pepsi_match.group(1)
    #    drink_type = pepsi_match.group(2)
    #    dt = datetime.utcnow()
        #slack_client.api_call("chat.postMessage", channel=channel, text="I don't understand. Pepsi command is '{num} cans of {drink type}'", as_user=True)

    #    user_model = get_user(user)
    #    drink_model = get_drink_type(drink_type)
    #    purchase = add_purchase(
    #        buyer=user_model,
    #        drink_type=drink_model,
    #        purchase_date=dt,
    #        num_cans=num
    #    )
    #    if purchase:
    #        slack_client.api_call("chat.postMessage", channel=channel,

    #                              text="%s bought %s cans of %s on %s" % (user, num, drink_type, dt.strftime("%A, %m-%d %H:%M")), as_user=True)
    #    else:
    #        slack_client.api_call("chat.postMessage", channel=channel,

    #                            text="Purchase failed!")
    #elif re.match(add_for_user_command_string, command.lower()) is not None:
    #    match = re.match(add_for_user_command_string, command.lower())
    #    username = match.group(1)
    #    num = match.group(2)
    #    drink_type = match.group(3)
    #    dt = datetime.utcnow()

    #    user_model = get_user(username)
    #    drink_model = get_drink_type(drink_type)
    #    purchase = add_purchase(
    #        buyer=user_model,
    #        drink_type=drink_model,
    #        purchase_date=dt,
    #        num_cans=num
    #    )

    #    if purchase:
    #        slack_client.api_call("chat.postMessage", channel=channel,

    #                              text="%s bought %s cans of %s on %s" % (user_model.username, num, drink_type, dt.strftime("%A, %m-%d %H:%M")), as_user=True)
    #    else:
    #        slack_client.api_call("chat.postMessage", channel=channel,

    #                            text="Purchase failed!")
    def get_user(self, username):
        try:
            with db.atomic():
                return User.create(username=username)
        except ieerror:
            return User.get(User.username == username)

    def get_drink_type(self, drink_type):
        try:
            with db.atomic():
                return DrinkType.create(name=drink_type)
        except ieerror:
            return DrinkType.get(DrinkType.name == drink_type)

    def add_purchase(self, buyer, drink_type, purchase_date, num_cans):
        try:
            with db.atomic():
                return Purchase.create(buyer=buyer, drink_type=drink_type, purchase_date=purchase_date, num_cans=num_cans)
        except ieerror as ie:
            logger.debug("Error: %s", ie.message)
            return None
