# Screenscraper infrastructure
import json
import sys
import os
import imp
import re
import hashlib
from datetime import datetime, date, time
from argparse import ArgumentParser
from urllib2 import urlopen

class ScraperBase(object):
    """Base class for screenscraper implementations"""
    scraped_events = []
    
    # Default venue and category that can be set by derived class
    venue = None
    category = None

    def __init__(self):
        pass

    def add_event(self, name, description, occurrences, origin_key=None, venue=None, category=None, website=None, ticket_website=None, ticket_details=None):
        """
        Constructs an event record and adds it to the scraped_events array

        Name, description and occurrences are required. Occurrences should be a list of
        dictionaries created with occurrence(). If venue or category is not specified
        the default (self.venue/self.category) is used.
        """
        assert name is not None
        assert description is not None
        assert occurrences is not None

        new_event = { 'name' : name,
                      'description' : description, 
                      'occurrences' : occurrences,
                    }

        if venue is None:
            if self.venue is not None:
                new_event['venue'] = self.venue
        else:
            new_event['venue'] = venue

        if category is None:
            if self.category is not None:
                new_event['category'] = self.category
        else:
            new_event['category'] = category

        if website is not None: new_event['website'] = website
        if ticket_website is not None: new_event['ticket_website'] = ticket_website
        if ticket_details is not None: new_event['ticket_details'] = ticket_details

        if origin_key is not None:
            origin_key = self.name + '|' + origin_key
            if len(origin_key) > 40:
                sha1 = hashlib.sha1()
                sha1.update(origin_key)
                origin_key = sha1.hexdigest()
            new_event['origin_key'] = origin_key

        self.scraped_events += [new_event]

    def occurrence(self, start_date, start_time=None, end_date=None, end_time=None):
        """
        Construct an occurrence record for an event.

        If start_date is a datetime and start_time is not specified, the time field of 
        start_date will be used instead; same thing for end_date/end_time. All fields
        except for start_date are optional.

        Returns a dictionary which can be JSON-serialized as part of an event record.
        """
        assert start_date is not None

        new_occurrence = {}

        new_occurrence['start_date'] = start_date.strftime("%Y-%m-%d")

        if start_time is not None:
            new_occurrence['start_time'] = start_time.strftime("%H:%M")
        elif isinstance(start_date, datetime):
            new_occurrence['start_time'] = start_date.strftime("%H:%M")

        if end_date is not None:
            new_occurrence['end_date'] = end_date.strftime("%Y-%m-%d")

        if end_time is not None:
            new_occurrence['end_time'] = end_time.strftime("%H:%M")
        elif isinstance(end_date, datetime):
            new_occurrence['end_time'] = end_date.strftime("%H:%M")

        return new_occurrence

    def scrape(self, from_date, to_date):
        """
        Perform screenscraping (must be overridden by implementation class)

        from_date/to_date are optional and are time range hints. It's OK to return events from
        outside this range if available and does not require any more requests.

        The override method should add any events it has discovered into self.scraped_events.
        The easiest way of doing this is by calling add_event().
        """
        raise NotImplementedError("Derived scraper class must implement scrape()!")

    def get_test_data(self, from_date=None, to_date=None):
        self.save_local_data = True
        self.scrape(from_date, to_date)

    def make_local_filename(self, url):
        # get rid of problematic characters; deal with urlencoded special characters
        url_cleaned = re.sub('[^\w\d.]+|%[0-9a-fA-F]{2}', '_', url)

        # create directory for test data to live in, if required
        if not os.path.exists(self.name + '.testdata'):
            os.mkdir(self.name + '.testdata')

        return os.path.join(self.name + '.testdata', url_cleaned)

    def fetch(self, url, description=None):
        if not self.use_local_data:
            if description is None:
                print "Retrieving %s..." % url,
            else:
                print "Retrieving %s (%s)..." % (url,description),

            data = urlopen(url).read()
            print "got %d bytes" % len(data),

            if self.save_local_data:
                with open(self.make_local_filename(url), "w") as f:
                    f.write(data)
                    print " (saved to local store)"
            else:
                print ""

        else:
            data = open(self.make_local_filename(url)).read()
            if description is None:
                print "Retrieved %s from local store" % url
            else:
                print "Retrieved %s (%s) from local store" % (url,description)

        return data

    def get_month_list(self, from_date, to_date):
        if from_date is None:
            from_date = datetime.today()
        if to_date is None:
            to_date = datetime.today()

        month = from_date.month
        year = from_date.year
        months = []

        while month <= to_date.month and year <= to_date.year:
            months += [ (month,year) ]
            if month == 12:
                month = 1
                year += 1
            else:
                month += 1

        return months

    def to_json(self):
        return json.dumps(self.scraped_events, separators=(',', ':'))

def main():
    parser = ArgumentParser()
    parser.add_argument('scraper_name')
    parser.add_argument('--test', '-t', dest='use_local', action='store_true')
    parser.add_argument('--save-test', '-s', dest='save_local', action='store_true')
    parser.add_argument('--from-date', '-F', dest='from_date')
    parser.add_argument('--to-date', '-T', dest='to_date')

    args = parser.parse_args()

    filename = args.scraper_name + '.py'

    try:
        mod = imp.load_source('scraper_module', filename)
    except IOError:
        print "Could not find scraper implementation file '%s'" % filename
        return

    scraper = mod.get_scraper()
    
    # Test/debug data
    scraper.name = args.scraper_name
    scraper.use_local_data = args.use_local

    # Date range
    if args.from_date is not None:
        from_date = datetime.strptime(args.from_date, "%Y-%m-%d")
    else:
        from_date = None

    if args.to_date is not None:
        to_date = datetime.strptime(args.to_date, "%Y-%m-%d")
    else:
        to_date = None

    if not args.save_local:
        scraper.scrape(from_date, to_date)
        json = scraper.to_json()
        with open(args.scraper_name + ".json", "w") as f:
            f.write(json)
    else:
        scraper.get_test_data(from_date, to_date)

if __name__ == '__main__':
    main()
