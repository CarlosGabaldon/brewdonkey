#!/usr/bin/env python
# encoding: utf-8
"""
brew_handler.py

Local web server: python ~/google_appengine/dev_appserver.py ~/projects/brewdonkey/

Deploying: python ~/google_appengine/appcfg.py update ~/projects/brewdonkey/

Created by  on 2009-01-19.
Copyright (c) 2009 __BrewDonkey.com__. All rights reserved.
"""
import os
import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.api import users
import models
import brew_fetcher

template.register_template_library('templatetags.model_tags')


class NavItem(object):
    """Nav item"""
    def __init__(self, text, path):
        self.text = text
        self.path = path


class Handler(webapp.RequestHandler):

    nav = [NavItem(text="Login", path="#"),
           NavItem(text="Search", path="/beer/search"),
           #NavItem(text="New", path="/beers/new"),
           NavItem(text="All", path="/beers/all"),
           NavItem(text="Popular", path="/")]

    def render(self, template_name, response=None):

        if response is None:
            response = {}

        if users.get_current_user():
            self.nav[0].path  = users.create_logout_url(self.request.uri)
            self.nav[0].text  = 'Logout'
        else:
            self.nav[0].path  = users.create_login_url(self.request.uri)
            self.nav[0].text = 'Login'

        response["nav"] = self.nav
        response["path"] = self.request.path
        response["user"] = users.get_current_user()


        path = os.path.join(os.path.dirname(__file__), template_name)
        self.response.out.write(template.render(path, response))



class PopularHandler(Handler):

    def get(self):

        #self.response.out.write(dir(self.request))
        #self.response.out.write(self.request.accept)
        #return

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

class ListHandler(Handler):

    def get(self):

        beers = models.Beer.find_all()

        response = dict(beers=beers)

        self.render(template_name='templates/list.html', response=response)

class BulkHandler(Handler):

    def get(self):

        beers = brew_fetcher.fetch_beers()
        beer_list = []
        for i in range(0, len(beers), 2):
            items = beers[i:i+2]
            beer = models.Beer(name=str(items[1].contents[0]),
                           description="This is a new beer",
                           abv=float(0),
                           ibu=int(0),
                           video="None Provided",
                           permalink= items[1].contents[0].strip().replace(' ', '-'))

            brewery = models.Brewery(name=str(items[0].contents[0]),
                                     website="None Provided",
                                     address="None Provided")
            brewery.put()
            beer.brewery = brewery
            beer.put()
            beer_list.append(beer)

        response = dict(beers=beer_list)

        self.render(template_name='templates/list.html', response=response)

class NewHandler(Handler):

    def get(self):

        self.render(template_name='templates/new.html')

class CreateHandler(Handler):

    def post(self):
        beer = models.Beer(name=self.request.get('name'),
                           description=self.request.get('description'),
                           abv=float(self.request.get('abv')),
                           ibu=int(self.request.get('ibu')),
                           video=self.request.get('video'),
                           permalink = self.request.get('name').strip().replace(' ', '-'))

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
        beers = models.Beer.search(query=query)
        response = dict(beers=beers, query=query)
        self.render(template_name='templates/search.html', response=response)


class VoteHandler(Handler):

    def get(self, permalink):

        beer = models.Beer.find_by(attribute="permalink", value=permalink)

        if beer is None:
            self.render(template_name='templates/404.html')
            return

        if models.Election.has_voted(user=users.get_current_user(), beer=beer):
            self.redirect('/')
            return

        votes = models.Election.vote(user=users.get_current_user(), beer=beer)


        json_response = """{'beer': '%s',
                            'votes': '%s' }""" % (beer.permalink, votes)

        self.response.out.write(json_response)

        #if self.ajax_request:
           # self.response.out.write(json_response)
        #else:
        #    self.redirect('/')


class ViewHandler(Handler):

    def get(self, permalink):

        beer = models.Beer.find_by(attribute="permalink", value=permalink)

        if beer is None:
            self.render(template_name='templates/404.html')
            return

        response = dict(beer=beer)
        self.render(template_name='templates/view.html', response=response)



class ProfileHandler(Handler):

    def get(self, user_name):

        profile = models.Profile.find_by_user_name(user_name=user_name)

        if profile is None:
            self.render(template_name='templates/404.html')
            return

        response = dict(profile=profile)
        self.render(template_name='templates/profile.html', response=response)

class NotFoundHandler(Handler):

    def get(self):
        self.render(template_name='templates/404.html')


def main():

    application = webapp.WSGIApplication([
        ('/', PopularHandler),
        ('/people/(.*)', ProfileHandler),
        ('/beers/popular', PopularHandler),
        ('/beers/all', ListHandler ),
        ('/beers/new', NewHandler),
        ('/beers/create', CreateHandler),
        ('/beers/bulk', BulkHandler),
        ('/beers/edit', EditHandler),
        ('/beers/update', UpdateHandler),
        ('/beer/search', SearchHandler),
        ('/vote/(.*)', VoteHandler),
        ('/beer/([^/]+)/*$', ViewHandler),
        ('/.*', NotFoundHandler)], debug=True)

    run_wsgi_app(application)



if __name__ == '__main__':
  main()

