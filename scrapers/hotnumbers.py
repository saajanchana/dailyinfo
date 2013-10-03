from scraper import ScraperBase
from datetime import datetime
from bs4 import BeautifulSoup
import re

class HotNumbersScraper(ScraperBase):
    def scrape(self, from_date, to_date):
        self.venue = 'Hot Numbers'
        self.category = 'Gigs'

        raw = self.fetch("http://hotnumberscoffee.co.uk/live-music/")
        soup = BeautifulSoup(raw)

        for ev_node in soup("article", class_="eventlist-event"):
            ev_spec = {}
            title_node = ev_node.h1.a

            # Get event name and strip time info from the end - we extract it from metadata below
            ev_spec['name'] = re.sub(r'\s*\d\d:\d\d - \d\d:\d\d', '', title_node.string)
            ev_spec['website'] = 'http://hotnumberscoffee.co.uk' + title_node['href']
            ev_spec['origin_key'] = title_node['href']

            # concatenate all <p>s inside all div.html_block to form description
            ev_spec['description'] = ""
            for div in ev_node("div", class_="html-block"):
                for p in div("p"):
                    ev_spec['description'] += str(p)  # FIXME - ought to sanitize this somewhere
            ev_spec['description_is_html'] = True

            # timing details are in hidden <time> tags
            occ_spec = {}
            meta_node = ev_node.find("ul", class_="eventlist-meta")
            date_str = meta_node.find("time", class_="event-meta-heading").get_text()
            occ_spec['start_date'] = datetime.strptime(date_str, "%A, %B %d, %Y")
            time_str = meta_node.find("time", class_="event-time-24hr").get_text()
            times = time_str.split(u'\u2013')  # &ndash;
            occ_spec['start_time'] = datetime.strptime(times[0].strip(), "%H:%M")

            if len(times) > 1:
                occ_spec['end_time'] = datetime.strptime(times[1].strip(), "%H:%M")

            ev_spec['occurrences'] = [self.occurrence(**occ_spec)]

            # all done
            self.add_event(**ev_spec)

def get_scraper(*args): # factory method
    return HotNumbersScraper()
