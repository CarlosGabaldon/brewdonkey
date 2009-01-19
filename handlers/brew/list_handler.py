#!/usr/bin/env python
# encoding: utf-8
"""
list_handler.py

Created by  on 2009-01-19.
Copyright (c) 2009 __brewdonkey.com__. All rights reserved.
"""
import wsgiref.handlers
from google.appengine.ext import webapp


class ListHandler(webapp.RequestHandler):

  def get(self):
    self.response.out.write('Brew donkey')


def main():
  application = webapp.WSGIApplication([('/', ListHandler)],
                                       debug=True)
  wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
  main()

