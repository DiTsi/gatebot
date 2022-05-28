#!/usr/bin/python2

import mraa
import logging
import requests
import threading
import json
from time import sleep


BOT_TOKEN = 'nopass'
# GROUP = -629434310
GROUP = -nogroup #! test group
SILENT = True
ENABLE_BUTTON_NOTIFICATION = True


class Bot:
    def __init__(self, token):
        self.token = token
        self.link = "https://api.telegram.org/bot" + self.token


    def get_updates(self, offset=None):
        r = requests.get(self.link + "/getUpdates", params={"offset": offset})
        content = json.loads(r.content.decode())

        return content['result']


    def send_message(self, chat_id, message):
        r = requests.get(self.link + "/sendMessage", params={
            'chat_id': chat_id,
            'text': message,
            })


def filter_mentions(updates):
    for u in updates:
        message = u['message']
        if 'entities' not in message.keys():
            updates.remove(u)
            continue
        if message['entities'][0]['type'] != 'mention':
            updates.remove(u)
    return updates


def filter_group(updates, group_id):
    for u in updates:
        message = u['message']
        if message['chat']['id'] != group_id:
            updates.remove(u)
    return updates


def get_last_id(updates):
    return updates, updates[-1]['update_id'] if len(updates) else None


def get_messages(updates):
    messages = []
    for u in updates:
        messages.append(u['message'])
    return messages


def enable_notification():
    global ENABLE_BUTTON_NOTIFICATION
    
    ENABLE_BUTTON_NOTIFICATION = True


def button_handler(userdata):
    global ENABLE_BUTTON_NOTIFICATION

    if ENABLE_BUTTON_NOTIFICATION:
        ENABLE_BUTTON_NOTIFICATION = False
        logging.info('button pressed')
        bot.send_message(GROUP, 'Button pressed, please open the gate')
        timer.start()



bot = Bot(BOT_TOKEN)


logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level='INFO')
timer = threading.Timer(60.0, enable_notification)

# gate output
gate = mraa.Gpio(2)
gate.dir(mraa.DIR_OUT)

# button
pin = mraa.Gpio(3)
pin.dir(mraa.DIR_IN)
pin.isr(mraa.EDGE_FALLING, button_handler, None)

offset = None
while True:
    logging.info('getting messages')

    updates = bot.get_updates(offset=offset)
    updates = filter_mentions(updates)
    updates = filter_group(updates, GROUP)
    updates, last_id = get_last_id(updates)
    offset = last_id + 1 if last_id is not None else None

    messages = get_messages(updates)
    if len(messages):
        gate.write(1)
        sleep(0.5)
        gate.write(0)

        if not SILENT: bot.send_message(GROUP, 'done')
        logging.info('open / close gate')

    sleep(3)
