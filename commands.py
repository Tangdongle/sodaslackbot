import functools
from collections import deque
from copy import copy
import itertools
import re
from datetime import datetime
from peewee import IntegrityError as ieerror
from sodabot import slack_client

from models import User, Purchase, DrinkType, db
from config import logger

REGISTRY = {}

class NonCommandModuleException(Exception):
    pass

class CommandDecorator(object):
    __name__ = "Basic Command" #This exists so it more closely mimics a func

    def __init__(cls, new_command=None):
        logger.debug("%s is the new command", new_command)
        if isinstance(new_command, str) or new_command is None:
            return cls
        for attr in new_command.__dict__:
            if attr.startswith('_bc'):
                if not hasattr(cls, attr):
                    setattr(cls, attr, new_command.__dict__[attr])

class RegisterCommand(CommandDecorator):
    __name__ = "Register Command"

    def __init__(cls, command):
        cls._bc_registered_command = command
        super(RegisterCommand, cls).__init__(command)

    def __call__(cls, instance, *args, **kwargs):
        logger.debug("RegisterCommand Args: %s", args)
        logger.debug("RegisterCommand Kwargs: %s", kwargs)
        cls._bc_registered_command(instance, *args, **kwargs)
        return cls

class DefaultCommand(CommandDecorator):
    __name__ = "Default Command"

    def __init__(cls, command):
        #command._bc_default_command = command
        cls._bc_default_command = command
        super(DefaultCommand, cls).__init__(command)

    def __call__(cls, instance, *args, **kwargs):
        logger.debug("DefaultCommand Args: %s", args)
        logger.debug("DefaultCommand Kwargs: %s", kwargs)
        cls._bc_default_command(instance, *args, **kwargs)
        return cls

def default_command(func):
    logger.debug("Calling default command!")
    return DefaultCommand(func)

def register_command(func):
    logger.debug("Calling register command!")
    return RegisterCommand(func)

class PatternMustMatch(CommandDecorator):
    def __init__(cls, pattern, requires_validation=True):
        cls._bc_pattern_func = None
        cls._bc_pattern = pattern
        cls._bc_requires_validation = None
        cls._bc_initial_validation = requires_validation

    def syntax_error(cls, message, fn, *args, **kwargs):
        logger.debug("Syntax Error: %s : %s: %s", message, cls.__class__, message)

    def __call__(cls, command, *args, **kwargs):
        logger.debug("Dir(cls): %s", dir(cls))
        logger.debug("PatternMatch command: %s", command)
        logger.debug("PatternMatch Args: %s", args)
        logger.debug("PatternMatch KWArgs: %s", kwargs)
        #If our pattern is not set, we set it for the first time and we return the function
        def validate(command, *args, **kwargs):
            logger.debug("Validating pattern for %s", command)
            if cls._validate(command, args[0][0]):
                cls._bc_pattern_func(command, *args[0][0], **kwargs)
                return cls
            else:
                return cls.syntax_error("pattern must match error :: ", command, args, kwargs)

        if cls._bc_requires_validation:
            return validate(command, args, kwargs)
        else:
            if cls._bc_requires_validation is None:
                super(PatternMustMatch, cls).__init__(command)
                cls._bc_requires_validation = cls._bc_initial_validation
            if cls._bc_pattern_func is None:
                cls._bc_pattern_func = command
            return cls



    def _validate(cls, command, args):
        logger.debug("Validate Args: %s", args)
        if not cls._bc_pattern:
            return False
        else:
            if re.match(cls._bc_pattern, " ".join(args)) is not None:
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
        l = "%s: %s cans of %s on %s\n"
        total = ""
        for p in Purchase.select():
            total += l % (p.buyer.username, p.num_cans, p.drink_type.name, p.purchase_date.strftime("%A, %m-%d %H:%M"))

        slack_client.api_call("chat.postMessage", channel=self.channel,
                              text="Totals: \n%s" % total, as_user=True)

    @pattern_must_match('([a-zA-Z]+)?\s?(\d\d?) cans? of ([\w\s]+).*', True)
    @register_command
    def insert(self, *args, **kwargs):
        logger.debug("Insert args %s", args)
        logger.debug("Insert kwargs %s", kwargs)
        logger.debug("Insert self, %s", self)
        who = args[0]
        self.user = self.get_user(who)
        self.purchase(self, args[1:], kwargs)

    @pattern_must_match('(\d\d?) cans? of ([\w\s]+).*', True)
    @default_command
    @register_command
    def purchase(self, *args, **kwargs):
        logger.debug("self, %s", self)
        logger.debug("args %s", args)
        logger.debug("kwargs %s", kwargs)

        if self in [(), {}, (({}, ()), {})]:
            return

        command = kwargs.pop('command', None)

        num = args[0]
        drink_start = args.index('of') + 1
        drink_type = ' '.join(list(args)[drink_start:])

        user_model = self.user
        drink_model = self.get_drink_type(drink_type)
        dt = datetime.utcnow()

        logger.debug("Cans: %s", num)
        logger.debug("User Model: %s", user_model)
        logger.debug("Drink Type: %s", drink_model)
        logger.debug("dt: %s", dt)
        purchase = self.add_purchase(
            buyer=user_model,
            drink_type=drink_model,
            purchase_date=dt,
            num_cans=num
        )
        if purchase:
            slack_client.api_call("chat.postMessage", channel=self.channel, text="%s bought %s cans of %s on %s" % (self.user.username, num, drink_type, dt.strftime("%A, %m-%d %H:%M")), as_user=True)
        else:
            slack_client.api_call("chat.postMessage", channel=self.channel, text="Purchase failed!")
        return args

    def __init__(self, command, channel, user):
        if not isinstance(command, deque):
            command = deque(command)

        if not isinstance(user, User):
            user = self.get_user(user)

        self.channel = channel
        module_id = self._module_id.lower()
        logger.debug("COMMAND %s", command)

        self.user = user
        logger.debug("Registry: %s ", REGISTRY)

        command_name = command[0]
        logger.debug("%s has called for the %s command", user.username, command)
        commands = {
            'command': command_name
        }


        try:
            REGISTRY[module_id][command_name](self, *itertools.islice(command, 1, None), **commands)
        except KeyError as ie:
            try:
                commands['command'] = None
                REGISTRY[module_id]['default'](self, *command, **commands)
            except Exception as e:
                logger.error("Exception reached in module: %s %s", e, e.message)
                self.command_error(ie.message, command_name, commands=command)

    #### DB Wrapper functions ###
    def get_user(self, username):
        logger.debug("Getting user %s ",username)
        try:
            with db.atomic():
                return User.create(username=username)
        except ieerror:
            return User.get(User.username == username)

    def get_drink_type(self, drink_type):
        logger.debug("Getting Drinky Type %s ", drink_type)
        try:
            with db.atomic():
                return DrinkType.create(name=drink_type)
        except ieerror:
            return DrinkType.get(DrinkType.name == drink_type)

    def add_purchase(self, buyer, drink_type, purchase_date, num_cans):
        logger.debug("Creating purchase %s ",num_cans)
        try:
            with db.atomic():
                return Purchase.create(buyer=buyer, drink_type=drink_type, purchase_date=purchase_date, num_cans=num_cans)
        except ieerror as ie:
            logger.debug("Error: %s", ie.message)
            return None
