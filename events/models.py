from django.db import models
from django.utils import safestring
import django.core.urlresolvers as urlresolvers
from misc import date2str, time2str
from datetime import datetime, date, time
from bs4 import BeautifulSoup, NavigableString
import queries
import re

class Venue(models.Model):
    name = models.CharField('Name', max_length=100)
    address = models.CharField('Address', max_length=100, blank=True)
    website = models.URLField('Website', blank=True)
    phone = models.CharField('Phone number', max_length=50, blank=True)
    description = models.TextField('Description', blank=True)

    def this_week_events(self):
        """Returns events occurring in the next 7 days (can be used from a template)"""
        return queries.UpcomingEvents(venue=self, days=7)
        #return Event.objects.none()

    def __unicode__(self):
        return self.name

class Category(models.Model):
    name = models.CharField('Category name', max_length=25)
    description = models.TextField('Description', blank=True)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name_plural = "categories"

class Event(models.Model):
    name = models.CharField('Name', max_length=100)
    description = models.TextField('Description')
    origin_key = models.CharField('Origin key', max_length=40, blank=True)

    venue = models.ForeignKey(Venue)
    category = models.ForeignKey(Category)

    website = models.URLField('Website', blank=True)
    ticket_website = models.URLField('Ticket website', blank=True)
    ticket_details = models.CharField('Ticket details', max_length=100, blank=True)

    occurrence_range = (None, None)

    def set_occurrence_range(self, start_date=None, end_date=None):
        self.occurrence_range = (start_date, end_date)

    def occurrences_in_range(self):
        """
        Return occurrences limited to date range from set_occurrence_range (can be used from a template)
        """
        queryset = Occurrence.objects.filter(event=self)
        if self.occurrence_range[0] is not None:
            queryset = queryset.filter(start_date__gte=self.occurrence_range[0])
        if self.occurrence_range[1] is not None:
            queryset = queryset.filter(start_date__lte=self.occurrence_range[1])
        return queryset

    def description_full(self):
        return safestring.mark_safe(self.description)

    def word_count(self, text):
        if not (isinstance(text, str) or isinstance(text, NavigableString)):
            text = text.get_text()
        words = re.split(r'[\s]+', text)
        return len(words)

    def keep_first_nwords(self, tag, max_words):
        if self.word_count(tag) > max_words:
            words = 0

            to_remove = []
            for child in tag.children:
                # If we already have too many words, queue child for destruction
                if words >= max_words:
                    to_remove.append(child)

                # This child won't take us over our word limit, leave it alone
                elif words + self.word_count(child) <= max_words:
                    words += self.word_count(child)

                # We need to truncate this child
                elif isinstance(child, NavigableString):
                    word_list = re.split(r'[\s]+', child)
                    s = BeautifulSoup().new_string(" ".join(word_list[0:(max_words-words)]) )
                    #print 'Truncating string %d => %d words' % (len(word_list), max_words - words)
                    child.replace_with(s)
                    words = max_words

                else: # It's a tag
                    #print 'Recursing into tag %s (max_words = %d)' % (str(child), max_words - words)
                    self.keep_first_nwords(child, max_words - words)
                    words = max_words

            map(lambda x: x.extract(), to_remove)
            return True    # tag was truncated
        else:
            return False

    def description_short(self):
        # get up to 20 words
        soup = BeautifulSoup(self.description)
        truncated = self.keep_first_nwords(soup, 50)

        if truncated:
            more_info_link = soup.new_tag('a', href=urlresolvers.reverse('event', kwargs = {'pk' : str(self.id)}))
            more_info_link['class'] = 'more_info_link'
            more_info_link.append('[...]')
            soup.append(more_info_link)

        # get rid of paragraphs
        for p_tag in soup.findAll('p'):
            p_tag.append(' ')  # ensure paragraph ends with a space before we flatten it
            p_tag.unwrap()

        return safestring.mark_safe(soup.decode(formatter='html'))

    @staticmethod
    def sanitise_html(text, is_html):
        if not is_html:
            # Plain text - generate HTML
            soup = BeautifulSoup()
            paras = text.split('\n')
            for para in paras:
                # Skip empty paragraphs
                if re.search(r'\S', para) is None:
                    continue
                
                tag = soup.new_tag("p")
                
                # Attempt to make links and add text to the tag
                while True:
                    mo = re.search(r'http://\S+', para)
                    if mo is None: 
                        # no links found - add remaining text to tag and finish
                        tag.append(soup.new_string(para))
                        break

                    # Add text before link (if any) as string
                    if mo.start() > 0:
                        tag.append(soup.new_string(para[:mo.start()]))

                    # Strip final punctuation off link target, if applicable
                    if re.match(r'.*[.,;/()]$', mo.group(0)) is not None:
                        link_href = para[ mo.start() : mo.end() - 1]
                        para = para[ mo.end() - 1:]
                    else:
                        link_href = mo.group(0)
                        para = para[ mo.end() :]

                    link_tag = soup.new_tag("a", href=link_href)
                    if len(link_href) <= 25:
                        link_tag.append(link_href)
                    else:
                        link_tag.append(link_href[:22] + '...')
                    tag.append(link_tag)

                soup.append(tag)

        else:
            # HTML - store sanitized HTML in the database
            blacklist = ['script', 'style']
            whitelist = { 'a' : ['href'],
                          'p' : None,
                          'div' : None,
                          'span' : None,
                          'br' : None,
                          'table' : None,
                          'tr' : None,
                          'td' : None,
                          'th' : None,
                          'thead' : None,
                          'tbody' : None,
                          'ul' : None,
                          'ol' : None,
                          'li' : None,
                          'b' : None,
                          'strong' : None,
                          'i' : None,
                          'em' : None,
                          'u' : None,
                          'strike' : None,
                        }

            soup = BeautifulSoup(text)

            for tag in soup.findAll():
                if tag.name.lower() in blacklist:
                    # remove including all children
                    tag.extract()
                elif tag.name.lower() not in whitelist:
                    # remove, retaining children
                    tag.unwrap()
                else:
                    # remove disallowed attributes
                    permitted_attrs = whitelist[tag.name.lower()]
                    for attr in tag.attrs:
                        if permitted_attrs is None or attr not in permitted_attrs:
                            del tag.attrs[attr]

        return soup.decode(formatter='html')

    @classmethod
    def add_from_json(cls, ev_spec):
        """
        Creates and saves an event from a dictionary. Raises an exception if there were any
        errors; you probably want to run this inside a transaction!

        Returns 'added', 'duplicate' or 'updated'.
        """
        # If an origin key was specified, see if the record already exists in the DB
        if 'origin_key' in ev_spec:
            q = Event.objects.filter(origin_key=ev_spec['origin_key'])
            if q.count() == 1:
                # TODO: check for updates here
                return 'duplicate'

        # FIXME: assumes the uploaded JSON was a valid event description...
        ev = cls(name=ev_spec['name'], description=cls.sanitise_html(ev_spec['description'], ev_spec['description_is_html']))

        # optional fields
        if 'origin_key' in ev_spec: ev.origin_key = ev_spec['origin_key']
        if 'website' in ev_spec: ev.website = ev_spec['website']
        if 'ticket_details' in ev_spec: ev.ticket_details = ev_spec['ticket_details']
        if 'ticket_website' in ev_spec: ev.ticket_website = ev_spec['ticket_website']

        # Set venue and category.
        if 'venue' in ev_spec:
            try:
                ev.venue = Venue.objects.get(name=ev_spec['venue'])
            except:
                raise Exception("Failed to add event '%s': could not find venue '%s'" % (ev_spec['name'], ev_spec['venue']))

        if 'category' in ev_spec:
            try:
                ev.category = Category.objects.get(name=ev_spec['category'])
            except:
                return Exception("Failed to add event '%s': could not find category '%s'" % (ev_spec['name'], ev_spec['category']))

        ev.save()

        # Process occurrences
        for occ_spec in ev_spec['occurrences']:
            occ = Occurrence()
            occ.start_date = datetime.strptime(occ_spec['start_date'], "%Y-%m-%d").date()
            if 'start_time' in occ_spec: occ.start_time = datetime.strptime(occ_spec['start_time'], "%H:%M").time()
            if 'end_date' in occ_spec: occ.end_date = datetime.strptime(occ_spec['end_date'], "%Y-%m-%d").date()
            if 'end_time' in occ_spec: occ.end_time = datetime.strptime(occ_spec['end_time'], "%H:%M").time()
            ev.occurrence_set.add(occ)

        return 'added'

    def __unicode__(self):
        return self.name

class Occurrence(models.Model):
    event = models.ForeignKey(Event)
    start_date = models.DateField('Start date')
    start_time = models.TimeField('Start time')
    end_date = models.DateField('End date', null=True, blank=True)
    end_time = models.TimeField('End time', null=True, blank=True)

    def is_past(self):
        """
        Work out whether an occurrence is in the past (can be called from a template)

        If end_date/end_time are set then return whether the event has finished,
        otherwise return whether or not the event has staretd
        """
        now = time(datetime.now().hour, datetime.now().minute)
        today = date.today()

        if self.start_date < today:
            if self.end_date is None or self.end_time is None:
                return True
            elif self.end_date < today or self.end_time < now:
                return True
            else:
                return False
        if self.start_date == today and self.start_time < now:
            if self.end_time is None:
                return True
            # check if event is still in progress
            if self.end_time > now:
                return False
        return False

    def long_string(self):
        return self.to_string(short=False)

    def to_string(self, short=True):
        ret = time2str(self.start_time)
        if self.end_time is not None and (self.end_date is None or self.end_date == self.start_date):
            ret += " - " + time2str(self.end_time)

        ret += " " + date2str(self.start_date, short=short)
        if self.end_date is not None and self.end_date != self.start_date:
            ret += " - "
            if self.end_time is not None:
                ret += time2str(self.end_time) + " "
            ret += date2str(self.end_date, short=short)
        return ret

    def __unicode__(self):
        return self.to_string(short=True)

    class Meta:
        ordering = ['start_date', 'start_time']