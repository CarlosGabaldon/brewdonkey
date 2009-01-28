#!/usr/bin/env python
#
# This software contains code derived from a CSV bulkload client
# (bulkload_client.py) developed for the Google App Engine by Google Inc.
#
# Copyright 2008 Garrett Davis
# Portions Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""
exporter - a.k.a. 'bulk downloader'

Downloads data from the Google App Engine datastore over HTTP,
as directed by requests from the bulk_download_client module.


"""


import os
try:
    # see if this was invoked by dev_appserver, or if running stand-alone
    serving = os.environ['SERVER_SOFTWARE']
except KeyError:
    # no 'server'defined; 
    # initialize & configure for unit testing
    serving = None
    import utest_init
    utest_init.setup_environ_stuff()
    print 'setup_environ_stuff() - ok'
    utest_init.setup_api_stuff()
    print 'setup_api_stuff() - ok'


import datetime, time
import logging
import csv
import StringIO

import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.ext import db   # import GqlQuery, _kind_map

# change this line to import your real model definition
from bulk_testdata import Employee, DowJonesHistory

ERROR_404_HTML = """
<HTML>
<HEAD>
</HEAD>
<BODY>
Sorry, that is not a legal address or request.
<p><p>
If you got this message by clicking on a link or button in this system,
please let us know what you did, so we can fix it.
</BODY>
</HTML>
"""

ERROR_500_HTML = """
<HTML>
<HEAD>
</HEAD>
<BODY>
Sorry, an error has occurred.
<!-- Status code {{err_status}}  -  {{err_descrip}}  -->
</BODY>
</HTML>
"""

RESPONSE_TEMPLATE = """\
%d items
more: %s
next-val: %s\
"""

#========================================

def parse_to_data_type(in_value, dbproperty):
    """ convert key value from a string to the internal Python data type
        based on its property
    """ 
    datatype = dbproperty.__class__.data_type
    if datatype is basestring:
        return in_value
    if datatype in (int, float):
        return datatype(in_value)
    # parse dates - we only support an ISO-like date format
    if datatype is datetime.date:
        return datetime.datetime(*time.strptime(in_value, "%Y-%m-%d")[0:3])
    if datatype is datetime.time:
        return datetime.datetime(*time.strptime(in_value, "%H:%M:%S")[0:6])
    if datatype == datetime.datetime:
        return datetime.datetime(*time.strptime(in_value, "%Y-%m-%d %H:%M:%S")
                                 [0:6])
    TRUTH_VALUES = {'yes': True, 'no': False, 'true': True, 'false': False}
    if datatype is bool:
        try:
            return TRUTH_VALUES[in_value.lower()]
        except KeyError:
            raise db.BadValueError, 'cannot convert to bool: ' + in_value

    # the db.property.validate routine can 'coerce' other property types,
    # if it cannot, we just can't handle it
    return dbproperty.validate(in_value)


def field_list_by_property_def(entity):
    """ generates a list of properties, in the order they were defined
    """
    field_list = list(key for key, val in sorted(
        entity.properties().items(), key=lambda x: x[1].creation_counter))
    #logging.debug(str(field_list))
    return field_list


def entity_data_to_csv(record_list, field_list=None,
                       quoting_option=csv.QUOTE_NONNUMERIC):
    """ converts values for a list of models to CSV format
    """
    if not record_list: return ''
    if not field_list:
        field_list = field_list_by_property_def(record_list[0])
    # logging.debug(str(field_list))
    outbuffer = StringIO.StringIO() # csv.writer writes to a file-like object
    writer = csv.writer(outbuffer, field_list, quoting=quoting_option)
    for item in record_list:
        writer.writerow(list(getattr(item, field, '') for field in field_list))
    csv_text = outbuffer.getvalue()
    outbuffer.close()
    # logging.debug('CSV=\n' + csv_text)
    return csv_text


def entity_data_to_xml(record_list, field_list=None):                       
    """ converts values for a list of models to XML format
    """
    if not record_list: return ''
    if not field_list:
        field_list = field_list_by_property_def(record_list[0])

    def tagify(tag, val):
        return "<%s>%s</%s>" % (tag, val, tag)

    from xml.sax import saxutils
    def render_val(rec, field):
        return saxutils.escape(unicode(getattr(rec, field)))

    return "\n\n".join(tagify(rec.__class__.__name__,
                              "\n  " +
                              "\n  ".join(tagify(field, render_val(rec, field))
                                          for field in field_list) + "\n")
                       for rec in record_list)


# want data in a format other than CSV or XML?
# write another method that formats the data the way you want it


class ExportRequestHandler(webapp.RequestHandler):
    """Common get/put functions, template generation etc.
    """

    def get(self, *args):
        """ handle a GET request: 'dispatch' to the proper method """
        logging.debug("ExportRequestHandler - Start")

        format = self.request.get('format')
        if not format:
            format = 'CSV'  # default
        else:
            format = format.upper() 
        if format == 'CSV':
            data_formatter = entity_data_to_csv
        elif format == 'XML':
            data_formatter = entity_data_to_xml
        else:
            logging.error("invalid value for 'format': " + format)
            self.error(500)
            self.response.out.write(ERROR_500_HTML)
            return

        kind = self.request.get('kind')
        if not kind:
            logging.error("'kind' not found or invalid format")
            self.error(500)
            self.response.out.write(ERROR_500_HTML)
            return

        key_field = self.request.get('key')
        if not kind:
            logging.error("'key' not found or invalid format")
            self.error(500)
            self.response.out.write(ERROR_500_HTML)
            return

        limit_str = self.request.get('limit')
        try:
            limit_val = int(limit_str)
        except TypeError, ValueError:
            logging.error("'limit' not found or invalid format")
            self.error(500)
            self.response.out.write(ERROR_500_HTML)
            return

        # query limit = one more then download limit
        # so we know if there are more to come
        limit_requested = limit_val+1  

        start_str = self.request.get('start')

        if start_str:
            # convert to internal datatype, based on property type
            model_class = db._kind_map[kind]
            model_prop = getattr(model_class, key_field)
            start_val = parse_to_data_type(start_str, model_prop)
            q_str = ( "SELECT * from %s WHERE %s >:1 ORDER BY %s LIMIT %s" %
                      (kind, key_field, key_field, limit_requested) )
            args = [start_val]
        else:
            q_str = ( "SELECT * from %s ORDER BY %s LIMIT %s" %
                     (kind, key_field, limit_requested) )
            args = []

        logging.debug("GQL:" + str(q_str))
        try:
            query_results = db.GqlQuery(q_str, *args)
        except TypeError:
            logging.error("Query is invalid format:")
            self.error(500)
            self.response.out.write(ERROR_500_HTML)
            raise

        if logging.getLogger().getEffectiveLevel() <= logging.DEBUG: 
            logging.debug("Query results: %d items", query_results.count())
            for j, item in enumerate(query_results[0:limit_val]):
                logging.debug("Item #%d = %s", j+1, getattr(item, key_field))

        query_count = query_results.count()
        if query_count == 0:
            response_text = RESPONSE_TEMPLATE % (0, 'no', 'none')
        else:
            return_count = min(query_count, limit_val)
            more_signal = ('yes' if query_count > limit_val else 'no')
            formatted_data = data_formatter(query_results[0:return_count])
            last_key_val = getattr(query_results[return_count-1], key_field)
            response_text = ( RESPONSE_TEMPLATE %
                              (return_count, more_signal, last_key_val)
                              + '\n'
                              + formatted_data )
        
        self.response.out.write(response_text)


    def post(self, *args):
        """ POST not supported for export """ 
        self.error(405)
        self.response.out.write(ERROR_404_HTML)
        return

#----------------------------------------
# leftover development / test fixtures
#----------------------------------------

TEST_RESPONSE = """\
2 items
more: no
next-val: [n/a]
Al Adams, 101 First St, Appleton, AL, 10001
Bill Brown, 202 Second St, Bakersfield, CA, 94992 \
"""

TEST_CSV_DATA = """\
AW,Ashley Wilkes,M,1972-02-02,the boy next door,S,M,2
DS,Dilcey,M,1988-02-02,household servant,W,M,2
EO,Ellen O'Hara,F,1977-07-01,Scarlett's mother,M,M,4
GO,Gerald O'Hara,M,1977-07-01,Scarlett's father,M,M,4
MW,Melanie Wilkes,F,1984-04-04,friend / rival,S,M,2
PS1,Pork,M,1988-01-01,household servant,W,M,2
PS2,Prissy,F,1988-03-03,household servant,W,S,0
RB,Rhett Butler,M,1980-02-02,Hero or villain,S,M,2
SoH,Scarlett O'Hara,F,1971-01-01,Heroine,S,M,2
""".splitlines()


def yield_test_data(batch_size):
    for start_line in range(0, len(TEST_CSV_DATA), batch_size):
        print start_line, batch_size, len(TEST_CSV_DATA)
        yield TEST_CSV_DATA[start_line:start_line+batch_size]
    

def query_test_data(start_val, batch_size):
    for start_line in range(0, len(TEST_CSV_DATA), batch_size):
        print start_line, batch_size, len(TEST_CSV_DATA)
        yield TEST_CSV_DATA[start_line:start_line+batch_size]

#========================================

APP_LIST = [ ('.*', ExportRequestHandler), ]

def main():
  logging.getLogger().setLevel(logging.DEBUG)
  application = webapp.WSGIApplication(APP_LIST)
  wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
  main()

