
import urllib
import os
import wsgiref.handlers
from BeautifulSoup import BeautifulSoup

source_url = "http://www.oregonbrewfest.com/printable_beers.php"
#source_url = "http://www.oregonbrewfest.com/index2.php?p=beers"

class Beer_Mock(object):
    pass


def fetch_beers():
    sock = urllib.urlopen(source_url)
    beer_source = sock.read()
    sock.close()
    soup = BeautifulSoup(beer_source)
    return soup.findAll(['h2', 'a'])

def test_fetch():
    beers = fetch_beers()
    beer_list = []
    for i in range(0, len(beers), 2):
        items = beers[i:i+2]
        beer = Beer_Mock()
        beer.brewery = items[0].contents[0]
        beer.name = items[1].contents[0]
        beer_list.append(beer)


    for beer in beer_list:
        print "Brewery: %s produces this quality beer: %s" % (beer.brewery, beer.name)



if __name__ == "__main__":
    test_fetch()

