#!/usr/bin/python3
import mwclient
import json
import time
import acnxpost
import logging

logging.basicConfig(filename='debug.log', format='%(asctime)s %(levelname)s %(message)s', level=logging.INFO)
logging.info('=== RESTART ===')

with open('settings.json') as f:
    settings = json.load(f)
    logging.info('Settings loaded')

wiki = mwclient.Site(settings['site'], path=settings['path'], clients_useragent=settings['ua'])
wiki.login(settings['user'], settings['password'])
logging.info("Logged in to " + settings['site'] + " as user " + settings['user'])

while True:
    acnxpost.run(wiki)
    time.sleep(60)
