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
"""Downloads data from the Google App Engine datastore over HTTP.

Usage:
  %s [flags]

    --debug             Show debugging information. (Optional)
    --cookie=<string>   Whole Cookie header to supply to the server, including
                        the parameter name (e.g., "ACSID=..."). (Optional)
    --url=<string>      URL endpoint to post to for exporting data. (Required)
    --batch_size=<int>  Number of Entity objects to include in each post to
                        the URL endpoint. The more data per row/Entity, the
                        smaller the batch size should be. (Default 10)
    --kind=<string>     Name of the Entity object kind to put in the datastore.
                        (Required)
    --keyfield=<string> Name of the a 'key field' in the datastore,
                        which must uniquely identify each entity, 
                        and which must be indexed.  (Required)
    --filename=<path>   Path to the CSV file to store the downloaded data.
                        (Required) The file will be created, and will replace
                        any existing file with the same name.

The exit status will be 0 on success, non-zero on export failure.

Works with the GAWSH exporter module.
Please look there for documentation about how to setup the server side.
"""


import StringIO
import httplib
import logging
import csv
import getopt
import socket
import sys
import urllib
import urlparse

class Error(Exception):
  """Base-class for exceptions in this module."""


class ConnectError(Error):
  """An error has occured while trying to post data to the server."""


class BadServerStatusError(ConnectError):
  """The server has returned an error while exporting data."""


def request_export(host_port, uri, cookie, kind,
                   key_field, start_val, batch_size):
  """Sends an HTTP request to download a collection of Entity records.

  Args:
    host_port: String containing the "host:port" pair; the port is optional.
    uri: Relative URI to access on the remote host (e.g., '/export'). 
    cookie: String containing the Cookie header to use, if any.
    kind: Kind of the Entity records being posted.
    key_field: Name of the 'key' field,
            used for both the sort order and the start_key value
    start_val: Lowest value of key_id to download
   
  The client will send this request to the server:
    SELECT * from <kind> WHERE <key_field>  >= <start_val> 

  Raises:
    BadServerStatusError - if the server was contactable but returns an error.
    ConnnectError - if an error occurred while connecting to the server 
                    or reading or writing data.
  """
  logging.debug('Connecting to %s', host_port)

  GQL_TEMPLATE = "SELECT * from %s %s ORDER BY %s" 
  WHERE_CLAUSE_TEMPLATE = "WHERE %s > '%s'" 

  request_values = {"kind": kind, "key": key_field, "limit": batch_size }
  if start_val:  # first batch
    request_values["start"] = start_val

  ## TODO someday: append optional filters ##

  request_string = urllib.urlencode(request_values)
  logging.debug('Sending request:' + request_string)
  if cookie:
      headers = { 'Cookie': cookie }
  else:
      headers = {}

  # define the return values, so they exist, if an exception happens
  return_data, more_flag, next_key_val = '', False, ''

  try:
    connection = httplib.HTTPConnection(host_port)
    try:
      connection.request('GET', uri + '?' + request_string, headers=headers)
      response = connection.getresponse()

      status = response.status
      reason = response.reason
      content = response.read()
      if status != httplib.OK:
        raise BadServerStatusError('Received code %d: %s\n%s' % (
                                   status, reason, content))

      logging.debug('Received response code %d: %s', status, reason)
      logging.debug('Received content: \n%s', content)

      content_lines = content.splitlines()
      assert len(content_lines) >= 3
      item_count, item_count_tag = content_lines[0].split(" ")
      more_count_tag, more_signal = content_lines[1].split(" ")
      next_kyval_tag, next_key_val = content_lines[2].split(" ",1)
      assert item_count_tag == 'items', 'item_count_tag not found'
      assert more_count_tag == 'more:',  'more_count_tag not found'
      assert next_kyval_tag == 'next-val:',  'next_kyval_tag not found'
      assert len(content_lines)-3 == int(item_count), 'item_count incorrect'
      more_flag = (more_signal != 'no')
      return_data = content_lines[3:]
      logging.debug('Received %d items from http://%s%s',
                    int(item_count), host_port, uri)
      logging.debug('More to come: ' + str(more_flag))

    finally:
      connection.close()
  except (IOError, httplib.HTTPException, socket.error), e:
    logging.debug('Encountered exception accessing HTTP server: %s', e)
    raise ConnnectError(e)

  return return_data, more_flag, next_key_val


def split_url(url):
  """Splits an HTTP URL into pieces.

  Args:
    url: String containing a full URL string (e.g.,
      'http://blah.com:8080/stuff?param=1#foo')

  Returns:
    Tuple (netloc, uri) where:
      netloc: String containing the host/port combination from the URL. The
        port is optional. (e.g., 'blah.com:8080').
      uri: String containing the relative URI of the URL. (e.g., '/stuff').
  """
  scheme, netloc, path, query, fragment = urlparse.urlsplit(url)
  return netloc, path

def adjusted(content_line):
  """ just adds a line break before storing each line to the local disk file
      customize this, if needed, to change the format stored locally      
  """
  return content_line + '\n'


def get_exported_data(url,
                      cookie,
                      batch_size,
                      kind,
                      key_field,
                      destination):
  """Exports CSV data using a series of HTTP posts.

  Args:
    filename: File on disk to create/append the exported data.
    url: URL used to request the data.
    cookie: Full cookie header to use while connecting.
    batch_size: Maximum number of Entity objects to transmit with each request.
    kind: Entity kind of the objects being posted.
    destination: file (or file-like object), available for dependency injection.

  Returns:
    True if all entities were exported successfully; False otherwise.
  """
  success_flag = True
  host_port, uri = split_url(url)
  try:
    logging.info('Starting download; maximum %d entities per post', batch_size)
    start_val = None
    more_flag = True
    while more_flag:
      try:
        (content,
         more_flag, next_key_val) = request_export(host_port, uri, cookie,
                                                   kind, key_field,
                                                   start_val, batch_size)

        logging.info('Received %d entities', len(content))
        for content_line in content:
          stored_line = adjusted(content_line)
          destination.write(stored_line)
          logging.debug('storing:' + stored_line)

        destination.flush()
        start_val = next_key_val
      except ConnectError, e:
        logging.error('An error occurred while downloading: %s', e)
        more_flag = False
        success_flag = False
  finally:
    destination.close()
  return success_flag


def PrintUsageExit(code):
  """Prints usage information and exits with a status code.

  Args:
    code: Status code to pass to sys.exit() after displaying usage information.
  """
  print sys.modules['__main__'].__doc__ % sys.argv[0]
  sys.stdout.flush()
  sys.stderr.flush()
  sys.exit(code)


def ParseArguments(argv):
  """Parses command-line arguments.

  Prints out a help message if -h or --help is supplied.

  Args:
    argv: List of command-line arguments.

  Returns:
    Tuple (url, filename, cookie, batch_size, kind) containing the values from
    each corresponding command-line flag.
  """
  opts, args = getopt.getopt(
    argv[1:],
    'h',
    ['debug',
     'help',
     'url=',
     'filename=',
     'cookie=',
     'batch_size=',
     'keyfield=',
     'kind='])

  url = None
  filename = None
  cookie = ''
  batch_size = 10
  kind = None
  encoding = None
  keyfield = None

  for option, value in opts:
    if option == '--debug':
      logging.getLogger().setLevel(logging.DEBUG)
    if option in ('-h', '--help'):
      PrintUsageExit(0)
    if option == '--url':
      url = value
    if option == '--filename':
      filename = value
    if option == '--keyfield':
      keyfield = value
    if option == '--cookie':
      cookie = value
    if option == '--batch_size':
      batch_size = int(value)
      if batch_size <= 0:
        print >>sys.stderr, 'batch_size must be 1 or larger'
        PrintUsageExit(1)
    if option == '--kind':
      kind = value

  return (url, cookie, batch_size, kind, keyfield, filename)


def main(argv):
  """Runs the exporter."""
  logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)-8s %(asctime)s %(filename)s] %(message)s')

  args = ParseArguments(argv)
  if [arg for arg in args if arg is None]:
    print >>sys.stderr, 'Invalid arguments'
    PrintUsageExit(1)

  url, cookie, batch_size, kind, keyfield, filename = args

  # Warning - no check if file already exists
  dest_file = open(filename, 'a')

  success = get_exported_data(url, cookie, batch_size,
                              kind, keyfield, dest_file)
  if success:
    logging.info('Export succcessful')
    return 0
  logging.error('Export failed')
  return 1


def run_unit_test():
  logging.getLogger().setLevel(logging.DEBUG)
  test_url = 'http://localhost:8080/export'
## to capture the data instead of writing a file ...  
##  dest = StringIO.StringIO()  

  dest = open('test_export.csv', 'w')
  get_exported_data(test_url, None, 5, 'Employee', 'vk', dest)


UNIT_TESTING = False

if __name__ == '__main__':
  if UNIT_TESTING:
    run_unit_test()
  else:
    sys.exit(main(sys.argv))

