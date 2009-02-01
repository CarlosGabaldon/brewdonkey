#!/usr/bin/env python
# encoding: utf-8
"""
models.py

Created by  on 2009-01-19.
Copyright (c) 2009 __BrewDonkey.com__. All rights reserved.
"""

from google.appengine.ext import db
from google.appengine.ext import search 

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
    votes = db.IntegerProperty()
    date_created = db.DateTimeProperty(auto_now_add=True)
    date_modified = db.DateTimeProperty(auto_now=True)
    
    def _number_of_votes(self):
           """Return number of votes."""
           vote_count = self.votes
           if vote_count is None:
               return 0
           else:
               return vote_count
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
         
         beer.votes = beer.votes + 1
         beer.put()
         election = Election(beer=beer, user=user)
         election.put()                                   
         return beer.votes

