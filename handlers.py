#!/usr/bin/env python
# encoding: utf-8
"""
brew_handler.py

Created by  on 2009-01-19.
Copyright (c) 2009 __BrewDonkey.com__. All rights reserved.
"""
import os
import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
import models

# design api with app.....

class ListHandler(webapp.RequestHandler):

    def get(self):
        
        beers = models.Beer.find_popular()
    
        # this will be the common api format...
        if self.request.get('format') == "xml":
            #refactor this into the models..to return xml or json or list
            #something like:
            #  beers = models.Beer.find_popular(format=xml)
            #  beers = models.Beer.find_popular(format=json)
            response = "<beers>"
            for beer in beers:
                response = response + beer.to_xml()
            response = response + "</beers>"
            self.response.out.write(response)
            return
        # common api...
            
        response = dict(beers=beers)
            

        path = os.path.join(os.path.dirname(__file__), 'templates/list.html')
        self.response.out.write(template.render(path, response))

class NewHandler(webapp.RequestHandler):

    def get(self):
    
        path = os.path.join(os.path.dirname(__file__), 'templates/new.html')
        self.response.out.write(template.render(path, None))

class CreateHandler(webapp.RequestHandler):

    def post(self):
        beer = models.Beer(name=self.request.get('name'),
                           description=self.request.get('description'))
                           
        brewery = models.Brewery(name=self.request.get('brewery_name'))
        beer.brewery = brewery
        beer.put()
        self.redirect('/')
    

class EditHandler(webapp.RequestHandler):

    def get(self):
        self.response.out.write('Edit Handler')
    
class UpdateHandler(webapp.RequestHandler):

    def get(self):
        self.response.out.write('Update Handler')

class SearchHandler(webapp.RequestHandler):

    def get(self):
        path = os.path.join(os.path.dirname(__file__), 'templates/search.html')
        self.response.out.write(template.render(path, None))

class VoteHandler(webapp.RequestHandler):

    def get(self):
        self.response.out.write('Vote Handler')


class ViewHandler(webapp.RequestHandler):

    def get(self):
        self.response.out.write('View Handler')

class NotFoundHandler(webapp.RequestHandler):
   
    def get(self):
        self.response.out.write("""We sorry, but we could not find the 
                                resource that you were looking for at
                                this url.""")
        

def main():

    application = webapp.WSGIApplication([
        ('/', ListHandler),
        ('/beers/list', ListHandler),
        ('/beers/new', NewHandler),
        ('/beers/create', CreateHandler),
        ('/beers/edit', EditHandler),
        ('/beers/update', UpdateHandler),
        ('/beers/search', SearchHandler),
        ('/beers/vote', VoteHandler),
        ('/beers/view', ViewHandler),
        ('/.*', NotFoundHandler)], debug=True)
                                       
    run_wsgi_app(application)
    


if __name__ == '__main__':
  main()

