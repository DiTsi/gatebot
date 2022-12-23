#!/usr/bin/python3

import os
import logging
from logging.handlers import TimedRotatingFileHandler
import requests
import json
import time


BOT_TOKEN = os.getenv('BOT_TOKEN')
GROUP = int(os.getenv('BOT_GROUP'))
SILENT = True
MESSAGE_TIMEOUT_SECONDS = 30
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


class Gate:
    def __init__(self, pinout):
        self.pinout = str(pinout)
        os.system(f'sudo echo {self.pinout} > /sys/class/gpio/export')
        os.system(f"sudo echo out > /sys/class/gpio/gpio{self.pinout}/direction")

    def open(self):
        os.system(f"echo 1 > /sys/class/gpio/gpio{self.pinout}/value")

    def close(self):
        os.system(f"echo 0 > /sys/class/gpio/gpio{self.pinout}/value")


class Bot:
    def __init__(self, token):
        self.token = token
        self.link = "https://api.telegram.org/bot" + self.token

    def get_updates(self, offset_=None):
        try:
            r = requests.get(self.link + "/getUpdates", params={"offset": offset_})
            content = json.loads(r.content.decode())
            return content['result']
        except Exception:
            logger.warning('Can\'t send GET request')
            return {}

    def send_message(self, chat_id, message):
        try:
            requests.get(self.link + '/sendMessage', params={
                'chat_id': chat_id,
                'text': message,
                })
        except Exception:
            logger.warning('Can\'t send message')


def filter_mentions(updates_):
    result = list()

    for u in updates_:
        if 'message' in u.keys():
            message = u['message']
            if 'entities' in message.keys():
                if message['entities'][0]['type'] == 'mention':
                    result.append(u)
    return result


def filter_group(updates_, group_id):
    result = list()

    for u in updates_:
        message = u['message']
        if message['chat']['id'] == group_id:
            result.append(u)
    return result


def filter_time(updates_):
    result = list()
    
    for u in updates_:
        message = u['message']
        if time.time() - int(message['date']) < MESSAGE_TIMEOUT_SECONDS:
            result.append(u)
    return result


def get_last_id(updates_):
    return updates_, updates_[-1]['update_id'] if len(updates_) else None


def get_messages(updates_):
    messages_ = list()
    for u in updates_:
        messages_.append(u['message'])
    return messages_


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


if __name__ == "__main__":
    DEBUG = False
    bot = Bot(BOT_TOKEN)
    logger = logging.getLogger('main_logger')
    logger.setLevel('INFO')
    rfh = TimedRotatingFileHandler('./logs/bot.log', when='midnight', backupCount=30)
    rfh.setFormatter(CustomFormatter())
    logger.addHandler(rfh)
    if not DEBUG:
        gate = Gate(227)

    # button
    # pin = mraa_.Gpio(3)
    # pin.dir(mraa_.DIR_IN)
    # pin.isr(mraa_.EDGE_FALLING, button_handler, None)
    # timer = threading.Timer(60.0, enable_notification)

    offset = None
    while True:
        logger.debug('getting messages')

        updates = bot.get_updates(offset_=offset)
        
        logger.debug(f'updates: {len(updates)}')
        filtered_updates = filter_mentions(updates)
        logger.debug(f'filter_mentions: {len(filtered_updates)}')
        filtered_updates = filter_group(filtered_updates, GROUP)
        logger.debug(f'filtered_updates: {len(filtered_updates)}')
        filtered_updates = filter_time(filtered_updates)
        logger.debug(f'filter_time: {len(filtered_updates)}')
        
        updates, last_id = get_last_id(updates)
        offset = last_id + 1 if last_id is not None else None

        messages = get_messages(filtered_updates)
        if len(messages):
            if not DEBUG:
                gate.open()
                time.sleep(0.25)
                gate.close()

            if not SILENT:
                bot.send_message(GROUP, 'done')
            logger.info('open / close gate')

        time.sleep(3)
