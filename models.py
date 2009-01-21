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
  logo = db.BlobProperty()
  
class Beer(db.Model):
  name = db.StringProperty(required=True)
  description = db.StringProperty(required=True, multiline=True)
  logo = db.BlobProperty()
  brewery = db.ReferenceProperty(Brewery)
  votes = db.IntegerProperty()
  date_created = db.DateTimeProperty(auto_now_add=True)
  date_modified = db.DateTimeProperty(auto_now=True)
  
  @classmethod
  def find_popular(cls):
      
      return db.GqlQuery("SELECT * FROM Beer ORDER BY votes DESC LIMIT 10")


# Example to access relationship
#beer = db.get(beer_key)
#brewery_name = beer.brewery.name