# Copyright (c) 2010 Adam Wisniewski (http://adamw523.com)
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import logging
import os
from google.appengine.ext import webapp
from google.appengine.api import memcache
from google.appengine.api.urlfetch import fetch
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template
from django.utils import simplejson as json

class MainHandler(webapp.RequestHandler):
  def get(self):
    self.response.out.write(template.render("views/index.html", {}))


class HandlerWithData(webapp.RequestHandler):
  def get_data(self):
    memcache.delete(self.data_key)
    data = memcache.get(self.data_key)
    if data is not None:
      return data
    else:
      data = self.query_for_data()
      memcache.add(self.data_key, data, 3600)
      return data

  def query_for_data(self):
    return fetch(self.data_url, None, 'GET', {}, False, True, 10).content
    
  def get(self):
    data = self.get_data()
    self.response.headers['Content-Type'] = self.data_content_type
    self.response.out.write(data)


class JsonHandler(HandlerWithData):
  data_url = 'http://api.scraperwiki.com/api/1.0/datastore/getdata?format=json&name=greenp_carparks&limit=500'
  data_key = 'json'
  data_content_type = 'application/json'


class KmlHandler(HandlerWithData):
  data_url = 'http://scraperwikiviews.com/run/toronto-green-p-locations-kml/?'
  data_key = 'kml'
  data_content_type = 'application/vnd.google-earth.kml+xml'


class GenerateKmlHandler(HandlerWithData):
  """Generating KML on GAE because KML view on ScraperWiki takes >10 seconds to generate"""
  def get(self):
    self.response.headers['Content-Type'] = 'application/vnd.google-earth.kml+xml'
    #self.response.headers['Content-Type'] = 'text/html'
    parsed_json = json.loads(self.get_json())
    self.response.out.write(template.render("views/carparks_kml.template", {'carparks': parsed_json}))
    
  def get_json(self):
    return JsonHandler().query_for_data()


def main():
  application = webapp.WSGIApplication([
    ('/', MainHandler),
    ('/feed.kml', KmlHandler),
    ('/feed.json', JsonHandler),
    ('/generatefeed.kml', GenerateKmlHandler)], debug=True)
  util.run_wsgi_app(application)


if __name__ == '__main__':
  main()
