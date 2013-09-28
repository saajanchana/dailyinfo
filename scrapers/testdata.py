from scraper import ScraperBase
from datetime import datetime, timedelta

class TestDataScraper(ScraperBase):
    def scrape(self):
        self.venue = 'Test Venue'
        self.category = 'Gigs'

        self.add_event(name='Event 1', description='Details of event 1', occurrences=[self.occurrence(datetime.now() + timedelta(days=1))])
        self.add_event(name='Event 2', description='Details of event 2', occurrences=[self.occurrence(datetime.now() + timedelta(days=8)),
                                                                                      self.occurrence(datetime.now() + timedelta(days=15)),
                                                                                      self.occurrence(datetime.now() - timedelta(days=3))] )

        self.add_event(name='Event 3', description='Details of event 3', website='http://website/', ticket_website='http://ticket-website/', 
                       ticket_details='£4-6 advance, £8-10 on the door', occurrences=[self.occurrence(datetime.now() + timedelta(days=4))])

def get_scraper(*args): # factory method
    return TestDataScraper()
