#!/usr/bin/python2

import telegram
import logging
from time import sleep

BOT_TOKEN = 'nopass'
# GROUP = -629434310
GROUP = -nogroup #! test group

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level='INFO')
bot = telegram.Bot(token=BOT_TOKEN)


def get_new_messages(bot_, update_id=None):
    try:
        updates = bot_.get_updates(allowed_updates=['message'], offset=update_id)
    except telegram.error.TimedOut:
        logging.warning('Timeout')
        return []
    return updates


def filter_mentions(updates):
    for u in updates:
        message = u['message']
        if len(message['entities']) == 0:
            updates.remove(u)
            continue
        if message['entities'][0]['type'] != 'mention':
            updates.remove(u)
    return updates


def filter_group(updates, group_id):
    for u in updates:
        message = u['message']
        if message['chat_id'] != group_id:
            updates.remove(u)
    return updates


def get_last_id(updates):
    return updates, updates[-1]['update_id'] if len(updates) else None


def get_messages(updates):
    messages = []
    for u in updates:
        messages.append(u['message'])
    return messages


if __name__ == '__main__':
    offset = None
    while True:
        logging.info('getting messages')

        updates = get_new_messages(bot, update_id=offset)
        updates = filter_mentions(updates)
        updates = filter_group(updates, GROUP)
        updates, last_id = get_last_id(updates)
        offset = last_id + 1 if last_id is not None else None

        messages = get_messages(updates)
        if len(messages):
            logging.info('open / close gate')

        sleep(4)
