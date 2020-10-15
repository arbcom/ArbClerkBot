#!/usr/bin/python3
import mwclient
import json
import time
import acnxpost
import logging
import os, requests
from http.cookiejar import MozillaCookieJar

logging.basicConfig(filename='debug.log', format='%(asctime)s %(levelname)s %(message)s', level=logging.INFO)
logging.info('=== RESTART ===')

with open('settings.json') as f:
    settings = json.load(f)
    logging.info('Settings loaded')

cookies_file = settings['cookie_path']

cookie_jar = MozillaCookieJar(cookies_file)
if os.path.exists(cookies_file):
    # Load cookies from file, including session cookies (expirydate=0)
    cookie_jar.load(ignore_discard=True, ignore_expires=True)
logging.info('We have %d cookies' % len(cookie_jar))

connection = requests.Session()
connection.cookies = cookie_jar  # Tell Requests session to use the cookiejar.

wiki = mwclient.Site(settings['site'], path=settings['path'], clients_useragent=settings['ua'], pool=connection)
if not wiki.logged_in:
	wiki.login(settings['user'], settings['bot_password'])
logging.info("Logged in to " + settings['site'] + " as user " + settings['user'])

# Save cookies to file, including session cookies (expirydate=0)
logging.info(connection.cookies)
cookie_jar.save(ignore_discard=True, ignore_expires=True)

acnxpost.run(wiki)
