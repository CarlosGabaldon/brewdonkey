#!/usr/bin/env python
# encoding: utf-8
"""
models.py

Created by  on 2009-01-19.
Copyright (c) 2009 __BrewDonkey.com__. All rights reserved.
"""

from google.appengine.ext import db

class Brewery(db.Model):
    name = db.StringProperty()
    address = db.PostalAddressProperty()
    website = db.StringProperty()
    logo = db.BlobProperty()
  
class Beer(db.Model):
    name = db.StringProperty(required=True)
    permalink = db.StringProperty()
    description = db.StringProperty(required=True, multiline=True)
    abv = db.FloatProperty()
    logo = db.BlobProperty()
    brewery = db.ReferenceProperty(Brewery)
    votes = db.IntegerProperty()
    date_created = db.DateTimeProperty(auto_now_add=True)
    date_modified = db.DateTimeProperty(auto_now=True)
        
    def _short_desc(self):
        """Return short description."""
        return  self.description[:150]
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
        

# Example to access relationship
#beer = db.get(beer_key)
#brewery_name = beer.brewery.name