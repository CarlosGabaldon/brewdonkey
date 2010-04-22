#!/usr/bin/env python
# encoding: utf-8
"""
unit_tests.py

Testing Console: http://localhost:8080/test

GAEUnit: http://code.google.com/p/gaeunit

Created by  on 2010-04-19.
Copyright (c) 2009 __BrewDonkey.com__. All rights reserved.
"""

import unittest
from google.appengine.api import users
import models


class BeerTest(unittest.TestCase):

    def setUp(self):
        self.permalink = 'Foo Beer'.strip().replace(' ', '-')
        self.beer = models.Beer(name='Foo Beer',
                               description='A light kung foo brew',
                               abv=20.2,
                               ibu=12,
                               video='None',
                               permalink = self.permalink)

        brewery = models.Brewery(name='Bar Brewery',
                                     website='http://foobar.com',
                                     address='1234 Foo Bar Way')

        brewery.put()
        self.beer.brewery = brewery
        self.beer.put()

    def tearDown(self):
        pass

    def test_new_beer(self):

        requested_beer = models.Beer.find_by(attribute="permalink",
                                             value=self.permalink)

        self.assertEquals(requested_beer.name, self.beer.name)

    def test_vote_for_beer(self):

        votes = models.Election.vote(user=users.get_current_user(),
                                     beer=self.beer)

        self.assertEquals(votes, self.beer.number_of_votes)

