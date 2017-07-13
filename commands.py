from functools import wraps
from copy import copy
import re

REGISTRY = {}

class register_command(object):
    def __init__(cls, command):
        cls._registered_command = command

#def pattern_must_match(pattern):
#    print pattern
#    def pattern_must_match_decorator(func):
#        @wraps(func)
#        def ret_fun(*args, **kwargs):
#            print args
#            return func(*args, **kwargs)
#        return ret_fun
#    return pattern_must_match_decorator

class pattern_must_match(object):

    def __init__(self, pattern):
        self._pattern = pattern
        print "init"

    def __call__(self, fn, *args, **kwargs):

        def ret_fun(*args, **kwargs):
            print self
            return fn(self, *args, **kwargs)
        return ret_fun

class MetaClass(type):
    def __init__(cls, name, bases, attrs):
        REGISTRY[name] = {}
        for key, val in attrs.iteritems():
            properties = getattr(val, '_registered_command', None)
            if properties is not None:
                REGISTRY[name][key] = properties

class BotCommandModule(object):
    __metaclass__ = MetaClass


class PepsiModule(BotCommandModule):

    _module_name = "Pepsi"

    @register_command
    def me(self, args):
        pass

    @register_command
    def list(self, args):
        print "TEST"

    @register_command
    @pattern_match('(\d\d?) cans? of ([\w\s]+).*')
    def purchase(self, args):
        pass


    def __init__(self, command, channel, user):
        self.command = command.popleft()
        self._registry = REGISTRY[self._module_name]
        print self._registry



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
