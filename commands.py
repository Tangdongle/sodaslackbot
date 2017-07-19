import functools
from collections import deque
from copy import copy
import re

from models import User, Purchase, DrinkType
from config import logger

REGISTRY = {}

class CommandDecorator(object):
    __name__ = "Basic Command" #This exists so it more closely mimics a func

    def __init__(cls, new_command=None):
        for attr in new_command.__dict__:
            if attr.startswith('_bc'):
                if not hasattr(cls, attr):
                    setattr(cls, attr, new_command.__dict__[attr])


class RegisterCommand(CommandDecorator):
    __name__ = "Register Command"

    def __init__(cls, command):
        #command._registered_command = command
        cls._bc_registered_command = command
        super(RegisterCommand, cls).__init__(command)

    def __call__(cls, *args, **kwargs):
        logger.debug("RegisterCommand args: %s", args)
        logger.debug("RegisterCommand command: %s", cls._bc_registered_command)
        cls._bc_registered_command(cls, args, kwargs)
        return cls

class DefaultCommand(CommandDecorator):
    __name__ = "Default Command"

    def __init__(cls, command):
        #command._bc_default_command = command
        cls._bc_default_command = command
        super(DefaultCommand, cls).__init__(command)

    def __call__(cls, *args, **kwargs):
        logger.debug("DefaultCommand args: %s", args)
        cls._bc_default_command(args, kwargs)
        return cls

def default_command(func):
    return DefaultCommand(func)

def register_command(func):
    return RegisterCommand(func)

class PatternMustMatch(CommandDecorator):
    def __init__(self, pattern, requires_validation=True):
        self._bc_pattern = pattern
        self._bc_requires_validation = None
        self._bc_initial_validation = requires_validation

    def syntax_error(self, message, fn, *args, **kwargs):
        logger.debug("Syntax Error: %s : %s in %s: %s", message, self.__class__, fn.__name__, message)

    def __call__(self, command, *args, **kwargs):
        #If our pattern is not set, we set it for the first time and we return the function
        def validate(command, *args, **kwargs):
            if self._validate(command, args, kwargs):
                command(args, kwargs)
                return self
            else:
                return self.syntax_error("pattern must match error :: ", command, args, kwargs)

        if self._bc_requires_validation:
            return validate(command, args, kwargs)
        else:
            if self._bc_requires_validation is None:
                super(PatternMustMatch, self).__init__(command)
                self._bc_requires_validation = self._bc_initial_validation
            logger.debug("PatternMatch args: %s", args)
            command(args, kwargs)
            return self



    def _validate(self, command, *args, **kwargs):
        if not self._bc_pattern:
            return False
        else:
            if re.match(self._bc_pattern, " ".join(args)) is not None:
                return True


def pattern_must_match(pattern, validate):
    return PatternMustMatch(pattern, validate)

class MetaClass(type):
    def __init__(cls, name, bases, attrs):
        if cls._module_id not in (None, ""):
            print "Adding %s to module list" % cls._module_id
            module_id = cls._module_id.lower()

            REGISTRY[module_id] = {}
            for key, val in attrs.iteritems():
                registered_command = getattr(val, '_bc_registered_command', None)

                #logger.debug("Key: %s | dir Val: %s | Type Val: %s", key, dir(val), type(val))
                if registered_command is not None:
                    REGISTRY[module_id][key] = registered_command

                default_command = getattr(val, '_bc_default_command', None)
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


    def command_error(self, message, command, *args, **kwargs):
        logger.debug("Unknown command with command %s and args %s: %s", command, args, message)

class PepsiCommand(BotCommandModule):

    _module_id = "Pepsi"

    @register_command
    def me(self, *args, **kwargs):
        pass

    @register_command
    def list(self, *args, **kwargs):
        print "TEST"

    @pattern_must_match('(\d\d?) cans? of ([\w\s]+).*', False)
    @default_command
    @register_command
    def purchase(self, *args, **kwargs):
        logger.debug("Purchase called with %s", args)

        #user_model = get_user(user)
        #drink_model = get_drink_type(drink_type)
        #purchase = add_purchase(
        #    buyer=user_model,
        #    drink_type=drink_model,
        #    purchase_date=dt,
        #    num_cans=num
        #)
        #if purchase:
        #    slack_client.api_call("chat.postMessage", channel=channel,

        #                          text="%s bought %s cans of %s on %s" % (user, num, drink_type, dt.strftime("%A, %m-%d %H:%M")), as_user=True)
        #else:
        #    slack_client.api_call("chat.postMessage", channel=channel,

        #                        text="Purchase failed!")
        #return args

    def __init__(self, command, channel, user):
        if not isinstance(command, deque):
            command = deque(command)

        module_id = self._module_id.lower()

        command_name = command[0]
        logger.debug("%s has called for the %s command", user.username, command)
        #logger.debug("Registry: %s", REGISTRY)

        try:
            REGISTRY[module_id][command_name](command[1:])
        except KeyError as ie:
            try:
                REGISTRY[module_id]['default'](command, *command)
            except Exception as e:
                self.command_error(ie.message, command_name, command)

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


    #    num = pepsi_match.group(1)
    #    drink_type = pepsi_match.group(2)
    #    dt = datetime.utcnow()
        #slack_client.api_call("chat.postMessage", channel=channel, text="I don't understand. Pepsi command is '{num} cans of {drink type}'", as_user=True)

    #    user_model = get_user(user)
    #    drink_model = get_drink_type(drink_type)
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
