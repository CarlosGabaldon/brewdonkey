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
import models

class BeerTest(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_new_beer(self):
        permalink = 'Foo Beer'.strip().replace(' ', '-')
        beer = models.Beer(name='Foo Beer',
                               description='A light kung foo brew',
                               abv=20.2,
                               ibu=12,
                               video='None',
                               permalink = permalink)

        brewery = models.Brewery(name='Bar Brewery',
                                     website='http://foobar.com',
                                     address='1234 Foo Bar Way')

        brewery.put()
        beer.brewery = brewery
        beer.put()

        requested_beer = models.Beer.find_by(attribute="permalink", value=permalink)

        self.assertEquals(requested_beer.name, beer.name)

