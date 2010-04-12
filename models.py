#!/usr/bin/env python
# encoding: utf-8
"""
models.py

Created by  on 2009-01-19.
Copyright (c) 2009 __BrewDonkey.com__. All rights reserved.
Local Datastore viewer: http://localhost:8080/_ah/admin/datastore
Remote Datastore viewer: https://appengine.google.com/dashboard?&app_id=brewdonkey&version_id=1.341161585300540618
"""

from google.appengine.ext import db
from google.appengine.ext import search

class Profile(db.Model):

    country_code = db.StringProperty()
    user = db.UserProperty(required=True)
    avatar = db.StringProperty()

    def _user_name(self):
        """Return the person's user name."""
        return self.user.name
    user_name = property(_user_name)

    def _get_full_name(self):
        """Return the person's full name."""
        return self.user.full_name
    full_name = property(_get_full_name)

    def _get_full_country_name(self):
        """Return the full country name."""
        from brewdonkey.form_choices import get_country_name
        return get_country_name(self.country_code)
    country = property(_get_full_country_name)

    def _beers_added(self):
        """Return the list of beers added by this person."""
        beers = []
        return beers
    beers_added = property(_beers_added)

    def _beers_voted_on(self):
        """Return the list of beers voted on by this person."""
        beers = []
        return beers
    beers_voted_on = property(_beers_voted_on)

    def _beers_commented_on(self):
        """Return the list of beers comment on by this person."""
        beers = []
        return beers
    beers_commented_on = property(_beers_commented_on)


    @classmethod
    def find_by_user_name(cls, user_name):

        profile = db.GqlQuery("SELECT * FROM Profile where user  = :1", user_name)

        if profile.count() == 0:
            return None
        else:
            return profile[0]


class Brewery(db.Model):
    name = db.StringProperty()
    address = db.PostalAddressProperty()
    website = db.StringProperty()
    logo = db.BlobProperty()

class Beer(search.SearchableModel):
    name = db.StringProperty(required=True)
    permalink = db.StringProperty()
    description = db.StringProperty(required=True, multiline=True)
    abv = db.FloatProperty()
    ibu = db.IntegerProperty()
    logo = db.BlobProperty()
    brewery = db.ReferenceProperty(Brewery)
    votes = db.IntegerProperty(default=0)
    date_created = db.DateTimeProperty(auto_now_add=True)
    date_modified = db.DateTimeProperty(auto_now=True)
    video = db.StringProperty()

    def _number_of_votes(self):
           """Return number of votes."""
           vote_count = self.votes
           if vote_count is None:
               return "%s votes" % 0
           elif vote_count == 1:
               return "%s vote" % str(vote_count)
           else:
               return "%s votes" % str(vote_count)
    number_of_votes = property(_number_of_votes)

    def _short_desc(self):
        """Return short description."""
        short = self.description[:150]
        if len(self.description) > len(short):
            return "%s..." % short
        else:
            return short
    short_desc = property(_short_desc)

    @classmethod
    def find_popular(cls):

        return db.GqlQuery("SELECT * FROM Beer ORDER BY votes DESC LIMIT 10")

    @classmethod
    def find_all(cls):

        return db.GqlQuery("SELECT * FROM Beer ORDER BY name ")


    @classmethod
    def find_by(cls, attribute, value):
        results = db.GqlQuery("SELECT * FROM Beer WHERE %s = :1" % attribute, value)

        if results.count() == 0:
            return None
        else:
            return results[0]

    @classmethod
    def search(cls, query):
        beers = Beer.all().search(query)
        return beers



class Election(db.Model):
     """
     Map if a user voted on a beer.

     """
     beer = db.ReferenceProperty(Beer)
     user = db.UserProperty(required=True)
     date_voted = db.DateTimeProperty(auto_now_add=True)

     @classmethod
     def has_voted(cls, user, beer):

        if not user: return False
        election = db.Query(Election)
        election.filter('beer =', beer)
        election.filter('user =', user)
        return election.get()

     @classmethod
     def vote(cls, user, beer):

         if beer.votes is None:
             beer.votes = 0

         beer.votes = beer.votes + 1
         beer.put()
         election = Election(beer=beer, user=user)
         election.put()
         return beer.number_of_votes

