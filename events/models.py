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
    colour = models.CharField('Colour', max_length=6)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name_plural = "categories"

class Event(models.Model):
    name = models.CharField('Name', max_length=100)
    description = models.TextField('Description')

    venue = models.ForeignKey(Venue)
    category = models.ManyToManyField(Category)

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