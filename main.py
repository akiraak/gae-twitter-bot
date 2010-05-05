#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
import wsgiref.handlers
from google.appengine.ext.webapp import template
import handler

def create_app(debug=True):
    return webapp.WSGIApplication(
        [
            ('/', handler.TopHandler),
            ('/jobs_local/cron-twitter', handler.CronTwitterHandler),
            ('/jobs_local/post-twitter', handler.PostTwitterHandler),
        ],
        debug=debug)

def main():
    util.run_wsgi_app(create_app())

if __name__ == '__main__':
    main()
