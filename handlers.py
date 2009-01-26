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


class NavItem(object):
    """Nav item"""
    def __init__(self, text, path):
        self.text = text
        self.path = path
        

class Handler(webapp.RequestHandler):
    
    nav = [NavItem(text="Login", path="#"),
           NavItem(text="Search", path="/beer/search"),
           NavItem(text="New", path="/beers/new"),
           NavItem(text="Popular", path="/")]

    def render(self, template_name, response=None):
        
        if response is None:
            response = {}
            
        response["nav"] = self.nav
        response["path"] = self.request.path
        
            
        path = os.path.join(os.path.dirname(__file__), template_name)
        self.response.out.write(template.render(path, response))


class ListHandler(Handler):

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
            
        self.render(template_name='templates/list.html', response=response)

class NewHandler(Handler):

    def get(self):
        
        self.render(template_name='templates/new.html')

class CreateHandler(Handler):

    def post(self):
        beer = models.Beer(name=self.request.get('name'),
                           description=self.request.get('description'),
                           abv=float(self.request.get('abv')),
                           permalink = self.request.get('name').strip().replace(' ', '+'))
                       
        brewery = models.Brewery(name=self.request.get('brewery_name'),
                                 website=self.request.get('website'),
                                 address=self.request.get('brewery_address'))  
        brewery.put()  
        beer.brewery = brewery
        beer.put()
        self.redirect('/')
    

class EditHandler(Handler):

    def get(self):
        self.response.out.write(self.request.path)
    
class UpdateHandler(Handler):

    def get(self):
        self.response.out.write('Update Handler')

class SearchHandler(Handler):

    def get(self):
        self.render(template_name='templates/search.html')
        
    def post(self):
        query = self.request.get('query')
        beers = models.Beer.find_by_query(query=query)
        response = dict(beers=beers, query=query)
        self.render(template_name='templates/search.html', response=response)
        

class VoteHandler(Handler):

    def get(self):
        self.response.out.write('Vote Handler')


class ViewHandler(Handler):

    def get(self):
        
        permalink = self.request.get("name").replace(' ', '+').strip()
        
        # self.response.out.write(permalink)
        #return
       
        if permalink is None:
            self.redirect('/') 
            
        
        beer = models.Beer.find_by(attribute="permalink", value=permalink)
        
        if beer is None:
            self.render(template_name='templates/404.html')
            return
        
        response = dict(beer=beer)
        self.render(template_name='templates/view.html', response=response)

class NotFoundHandler(Handler):
   
    def get(self):
        self.render(template_name='templates/404.html')
        

def main():

    application = webapp.WSGIApplication([
        ('/', ListHandler),
        ('/beers/list', ListHandler),
        ('/beers/new', NewHandler),
        ('/beers/create', CreateHandler),
        ('/beers/edit', EditHandler),
        ('/beers/update', UpdateHandler),
        ('/beer/search', SearchHandler),
        ('/beers/vote', VoteHandler),
        ('/beers/view', ViewHandler),
        ('/.*', NotFoundHandler)], debug=True)
                                       
    run_wsgi_app(application)
    


if __name__ == '__main__':
  main()

