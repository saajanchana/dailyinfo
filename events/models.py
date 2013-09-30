from django.db import models
from misc import date2str, time2str
from datetime import datetime, date, time
import queries

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

    @classmethod
    def add_from_json(cls, ev_spec):
        """
        Creates and saves an event from a dictionary. Returns the event or raises an
        exception if there were any errors; you probably want to run this inside a 
        transaction!
        """
        # FIXME: assumes the uploaded JSON was a valid event description...
        ev = cls(name=ev_spec['name'], description=ev_spec['description'])

        # optional fields
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