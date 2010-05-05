#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
import logging
import datetime
import wsgiref.handlers
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext import db
from google.appengine.api import urlfetch
from google.appengine.ext.webapp.util import login_required
from google.appengine.api.labs import taskqueue
from google.appengine.api import memcache
from settings import *
import random
import simplejson
import twoauth

class Globals(db.Model):
    last_username = db.StringProperty(required=True)
    last_text = db.StringProperty(required=True)
    last_created_at = db.StringProperty(required=True)

class Tweet(db.Model):
    tweet_id = db.IntegerProperty(required=True)
    text = db.TextProperty(required=True)

class TopHandler(webapp.RequestHandler):
    def get(self):
        self.response.out.write("hello!")

class CronTwitterHandler(webapp.RequestHandler):
    def get(self):
        run = True
        page = 1
        while run:
            url = 'http://search.twitter.com/search.json?page=' + str(page) + '&q=' + SEARCH_WORD
            self.response.out.write(url + "<br>")
            result = urlfetch.fetch(url)
            datas = simplejson.loads(result.content)
            self.response.out.write(result.content)
            self.response.out.write("<br><br><br><br>")

            globals = Globals.all().get()
            last_username = ""
            last_text = ""
            last_created_at = ""
            if globals:
                last_username = globals.last_username
                last_text = globals.last_text
                last_created_at = globals.last_created_at
            if result.status_code == 200 and datas['results']:
                if page == 1 and len(datas['results']) > 0:
                    data = datas['results'][0]
                    if globals:
                        globals.last_username = data['from_user']
                        globals.last_text = data['text']
                        globals.last_created_at = data['created_at']
                    else:
                        globals = Globals(
                            last_username = data['from_user'],
                            last_text = data['text'],
                            last_created_at = data['created_at']
                        )
                    globals.put()

                self.response.out.write('bbb<br>')
                for data in datas['results']:
                    self.response.out.write('ccc<br>')
                    if globals and last_username == data['from_user'] and  last_text == data['text'] and last_created_at == data['created_at']:
                        run = False
                        break
                    if TWITTER_USER != data['from_user']:
                        word_index = random.randint(0, len(RT_COMMENTS)-1)
                        word = RT_COMMENTS[word_index]
                        sendText = word + ' RT @' + data['from_user'] + " " + data['text']
                        tweet = Tweet(
                            tweet_id = data['id'],
                            text = sendText
                        )
                        tweet.put()
                        self.response.out.write('<img src="%s"> %s [%s] %s'%(data['profile_image_url'], data['id'], data['from_user'], data['text']))
                        self.response.out.write("<br><br>")
            else:
                run = False
            page = page + 1

class PostTwitterHandler(webapp.RequestHandler):
    def get(self):
        datas = Tweet.gql("ORDER BY tweet_id ASC")
        self.response.out.write("Hello!<br>")
        tw = None
        if datas:
            try:
                tw = twoauth.api(CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SERCRET)
            except Exception, e:
                text = str(e)
                self.response.out.write(text+"<br><br>")
                return
        for data in datas:
            try:
                sendText = data.text
                tw.status_update(sendText.encode("utf-8"), in_reply_to_status_id=data.tweet_id)
                self.response.out.write(sendText+"<br><br>")
            except Exception, e:
                try:
                    sendText = data.text[:100] + "..."
                    tw.status_update(sendText.encode("utf-8"), in_reply_to_status_id=data.tweet_id)
                    self.response.out.write(sendText+"<br><br>")
                except Exception, e:
                    text = str(e)
                    self.response.out.write(text+"<br><br>")
                    logging.warning(text)
            data.delete()

