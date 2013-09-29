from scraper import ScraperBase
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import re

class PortlandArmsScraper(ScraperBase):
    def scrape(self):
        self.venue = 'Portland Arms'
        self.category = 'Gigs'

        raw = self.fetch("http://www.theportlandarms.co.uk/mbbs2//calendar/calendar-view.asp?calendarid=3")
        calendar_soup = BeautifulSoup(raw)

        def is_event_link(tag):
            if tag.name == 'a':
                if tag.has_attr('href') and tag['href'].startswith("event-view.asp"):
                    return True
            return False

        # Extract event IDs. Some may be duplicates (for repeating events)
        event_ids = set()
        for ev_link_node in calendar_soup(is_event_link):
            mo = re.match(r'event-view.asp\?eventid=(\d+)', ev_link_node['href'])
            if mo is None:
                print "Warning: failed to extract event ID for event '%s'" % ev_link_node.string
                continue

            event_ids.add(mo.group(1))

        # Crawl all linked event pages
        for i, event_id in enumerate(event_ids):
            url = "http://www.theportlandarms.co.uk/mbbs2//calendar/event-view.asp?eventid=%s" % event_id
            raw = self.fetch(url, "event %d/%d" % (i, len(event_ids)))
            ev_soup = BeautifulSoup(raw)
            table_node = ev_soup.find("td", class_="maintable").find("table", class_="bbstable")

            ev_spec = { 'name' : table_node.find("td", class_="messagecellheader").get_text(),
                        'website' : url,
                      }

            # Extract event table fields into a dictionary
            table_fields = {}
            for row_node in table_node("tr"):
                if row_node.find("td", class_="messagecellbody") is None:  # this is the header row
                    continue
                key = re.sub(r'[^\w\s]', '', row_node.td.get_text()).lower().strip()
                value = row_node.td.next_sibling
                table_fields[key] = value

            ev_spec['description'] = "(Genre: %s) " % table_fields['genre'].get_text()
            ev_spec['description'] += table_fields['description'].get_text()
            ev_spec['ticket_details'] = table_fields['price info'].get_text()

            # Work out scheduling
            single_date = re.search(r'This event occurs once on (\d{1,2}/\d{1,2}/\d{4})', str(table_fields['event time']))
            start_time = re.search(r'\d{1,2}:\d\d - .M', str(table_fields['event time']))
            date_range = re.search(r'Occurs from (\d{1,2}/\d{1,2}/\d{4})\s*-\s*(\d{1,2}/\d{1,2}/\d{4})', str(table_fields['event time']))

            if start_time is None or (single_date is None and date_range is None):
                print "Warning: could not parse date info for event #%s (%s): <%s>" % (event_id, ev_spec['name'], str(table_fields['event time']))
                continue

            start_time_parsed = datetime.strptime(start_time.group(0), '%I:%M - %p')
            if single_date is not None:
                ev_spec['occurrences'] = [self.occurrence(start_date = datetime.strptime(single_date.group(1), '%d/%m/%Y'),
                                                          start_time = start_time_parsed)]
            else:
                # Create an occurrence for each day in the range
                first_date = datetime.strptime(date_range.group(1), '%d/%m/%Y')
                last_date = datetime.strptime(date_range.group(2), '%d/%m/%Y')
                ev_spec['occurrences'] = []
                d = first_date
                while d < last_date + timedelta(seconds=1):
                    ev_spec['occurrences'] += [self.occurrence(start_date = d, start_time = start_time_parsed)]
                    d += timedelta(days=1)

            self.add_event(**ev_spec)

def get_scraper(*args): # factory method
    return PortlandArmsScraper()
