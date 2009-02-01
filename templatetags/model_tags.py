#!/usr/bin/env python
# encoding: utf-8
"""
tags.py

Created by  on 2009-01-31.
Copyright (c) 2009 __MyCompanyName__. All rights reserved.
"""
from google.appengine.api import users
from google.appengine.ext.webapp import template
import models


# Get the template Library
register = template.create_template_register()


@register.inclusion_tag('beer.html')
def render_beer(beer, user, detail=False):
    """
     Inclusion tag for rendering a beer.

    Context::
        Beer

    Template::
        beer.html

    """
    user_can_vote = True
    #is_submitter_of_beer = False
    
    if user is not None:
        if models.Election.has_voted(user=user, beer=beer):
            user_can_vote = False
            #is_submitter_of_beer = beer.is_submitter_of_beer(user=user)
    else:
        user_can_vote = False
            
    
    return dict(beer=beer, detail=detail, user_can_vote=user_can_vote)
                #is_submitter_of_beer=is_submitter_of_beer)
