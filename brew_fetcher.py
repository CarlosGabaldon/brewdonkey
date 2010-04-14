
import urllib
import os
import wsgiref.handlers
from BeautifulSoup import BeautifulSoup

#source_url = "http://www.oregonbrewfest.com/printable_beers.php"
#source_url = "http://www.oregonbrewfest.com/index2.php?p=beers"
source_url = "http://www.oregonbrewfest.com/beers.php"

class Beer_Mock(object):
    pass


def fetch_beers():

    sock = urllib.urlopen(source_url)
    beer_source = sock.read()
    sock.close()
    soup = BeautifulSoup(beer_source)
    beers = soup.findAll(['h2', 'a',])
    beer_list = []
    for i in range(0, len(beers), 2):
        items = beers[i:i+2]
        beer = Beer_Mock()
        try:
            beer_info = items[0].contents[0].split('/')
            if beer_info[1].strip() != "TBA":
                beer.brewery = str(beer_info[0].strip())
                beer.name = str(beer_info[1].strip())
                beer.website = str(items[1].contents[0].strip())
                beer_list.append(beer)
        except IndexError:
            pass
        except TypeError:
            pass
    return beer_list

def test_fetch():

    beer_list = fetch_beers()
    for beer in beer_list:
        print "Brewery: %s Beer: %s Website: %s" % (beer.brewery, beer.name, beer.website)



if __name__ == "__main__":
    test_fetch()

