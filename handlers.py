#!/usr/bin/env python
# encoding: utf-8
"""
brew_handler.py

Created by  on 2009-01-19.
Copyright (c) 2009 __BrewDonkey.com__. All rights reserved.
"""
import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
import models



class ListHandler(webapp.RequestHandler):

    def get(self):
        
        self.response.out.write("""
            <html><body>
            <h2>Beers</h2>
            <ul>""")
        
        beers = models.Beer.find_popular()
        
        for beer in beers:
            self.response.out.write("<li>%s</li>" % beer.name)
            
        self.response.out.write("""
            </ul>  
            <a href='/new'>Add your beer</a>""")
    
class NewHandler(webapp.RequestHandler):

    def get(self):
    
        self.response.out.write("""
              <h2>Add your beer</h2>
              <form action="/create" method="post">
                <div>Beer name:<input type="text" id="name" name="name"/></div>
                <div>Beer desc:<textarea name="description" rows="3" cols="60"></textarea></div>
                <div><input type="submit" value="Submit"></div>
              </form>
            </body>
          </html>""")

class CreateHandler(webapp.RequestHandler):

    def post(self):
        beer = models.Beer(name=self.request.get('name'),
                           description=self.request.get('description'))
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
        self.response.out.write('Search Handler')

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
        ('/new', NewHandler),
        ('/create', CreateHandler),
        ('/edit', EditHandler),
        ('/update', UpdateHandler),
        ('/search', SearchHandler),
        ('/vote', VoteHandler),
        ('/view', ViewHandler),
        ('/.*', NotFoundHandler)], debug=True)
                                       
    run_wsgi_app(application)
    


if __name__ == '__main__':
  main()

