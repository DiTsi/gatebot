#!/usr/bin/python2

import mraa
import logging
from logging.handlers import TimedRotatingFileHandler
import requests
import threading
import json
import time


BOT_TOKEN = 'nopass'
GROUP = -nogroup #! "Parkovka. Bot" group
# GROUP = -nogroup #! "Parkovka" main group
# GROUP = -nogroup #! test group
# GROUP = -nogroup #! test group 2
SILENT = True
MESSAGE_TIMEOUT = 30 # seconds
# ENABLE_BUTTON_NOTIFICATION = True


class CustomFormatter(logging.Formatter):
    grey = "\033[37m"
    yellow = "\033[21m"
    white = "\033[97m"
    red = "\033[31m"
    bold_red = "\033[1m"
    reset = "\033[97m"
    format = "%(asctime)s\t%(levelname)s\t%(message)s"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: white + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


class Bot:
    def __init__(self, token):
        self.token = token
        self.link = "https://api.telegram.org/bot" + self.token


    def get_updates(self, offset=None):
        try:
            r = requests.get(self.link + "/getUpdates", params={"offset": offset})
            content = json.loads(r.content.decode())
            return content['result']
        except:
            logger.warning('Can\'t send GET request')
            return {}


    def send_message(self, chat_id, message):
        try:
            r = requests.get(self.link + "/sendMessage", params={
                'chat_id': chat_id,
                'text': message,
                })
        except:
            logger.warning('Can\'t send message')


def filter_mentions(updates):
    result = list()

    for u in updates:
        message = u['message']
        if 'entities' in message.keys():
            if message['entities'][0]['type'] == 'mention':
                result.append(u)
    return result


def filter_group(updates, group_id):
    result = list()

    for u in updates:
        message = u['message']
        if message['chat']['id'] == group_id:
            result.append(u)
    return result


def filter_time(updates):
    result = list()
    
    for u in updates:
        message = u['message']
        if time.time() - int(message['date']) < MESSAGE_TIMEOUT:
            result.append(u)
    return result


def get_last_id(updates):
    return updates, updates[-1]['update_id'] if len(updates) else None


def get_messages(updates):
    messages = []
    for u in updates:
        messages.append(u['message'])
    return messages


# def enable_notification():
#     global ENABLE_BUTTON_NOTIFICATION

#     ENABLE_BUTTON_NOTIFICATION = True


# def button_handler(userdata):
#     global ENABLE_BUTTON_NOTIFICATION

#     if ENABLE_BUTTON_NOTIFICATION:
#         ENABLE_BUTTON_NOTIFICATION = False
#         logger.info('button pressed')
#         bot.send_message(GROUP, 'Button pressed, please open the gate')
#         timer.start()

bot = Bot(BOT_TOKEN)

logger = logging.getLogger('main_logger')
logger.setLevel('INFO')
rfh = TimedRotatingFileHandler('/opt/telegram_bot/logs/bot.log', when='midnight', backupCount=7) # 1.7Mb per day with 'INFO' level
rfh.setFormatter(CustomFormatter())
logger.addHandler(rfh)

# timer = threading.Timer(60.0, enable_notification)

# gate output
gate = mraa.Gpio(2)
gate.dir(mraa.DIR_OUT)

# button
# pin = mraa.Gpio(3)
# pin.dir(mraa.DIR_IN)
# pin.isr(mraa.EDGE_FALLING, button_handler, None)

offset = None
while True:
    logger.debug('getting messages')

    updates = bot.get_updates(offset=offset)
    
    filtered_updates = filter_mentions(updates)
    filtered_updates = filter_group(filtered_updates, GROUP)
    filtered_updates = filter_time(filtered_updates)
    
    updates, last_id = get_last_id(updates)
    offset = last_id + 1 if last_id is not None else None

    messages = get_messages(filtered_updates)
    if len(messages):
        gate.write(1)
        time.sleep(0.25)
        gate.write(0)

        if not SILENT: bot.send_message(GROUP, 'done')
        logger.info('open / close gate')

    time.sleep(3)

