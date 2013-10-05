from datetime import date, datetime, timedelta
import json

from django.http import HttpResponse
from django.views import generic
from django import forms
from django.utils import safestring
from django.shortcuts import render
from django.db import transaction
import django.core.urlresolvers as urlresolvers

from models import *
from misc import date2str, time2str
import queries

class AllEventsView(generic.ListView):
    model = Event
    template_name = "events/event_list.html"

class PeriodView(generic.TemplateView):
    template_name = 'events/event_list.html'
    
    def get_context_data(self, **kwargs):
        context = super(PeriodView, self).get_context_data(**kwargs)

        if 'start_date' in self.kwargs and self.kwargs['start_date'] is not None:
            start_date = datetime.strptime(self.kwargs['start_date'], "%Y-%m-%d").date()
        else:
            start_date = date.today()

        end_date = start_date + timedelta(days=self.days - 1)

        context['start_date'] = start_date
        context['end_date'] = end_date

        # If available, get list of category IDs we're interested in
        wanted_categories = None
        if 'categories' in self.request.GET:
            try:
                wanted_categories = map(lambda x: int(x), self.request.GET['categories'].split(","))
            except ValueError:
                pass

        # If no category set has been specified, get everything within the date range
        if wanted_categories is None:
            context['event_list'] = queries.UpcomingEvents(start_date=start_date, end_date=end_date)
        else:
            context['event_list'] = queries.UpcomingEvents(start_date=start_date, end_date=end_date, categories=wanted_categories)

        context['next_url'] = urlresolvers.reverse(self.url_name, kwargs = {'start_date' : "{0:%Y-%m-%d}".format(start_date + timedelta(days=self.days))} )
        context['prev_url'] = urlresolvers.reverse(self.url_name, kwargs = {'start_date' : "{0:%Y-%m-%d}".format(start_date - timedelta(days=self.days))} )

        # If no category set has been specified, all categories are selected
        categories = Category.objects.all()
        if wanted_categories is None:
            # Return all categories
            wanted_categories = None
            for cat in categories:
                cat.active = True
        else:
            for cat in categories:
                if cat.id in wanted_categories:
                    cat.active = True
                else:
                    cat.active = False

        # See which categories we actually have in the date range
        available_categories = {}
        for ev in context['event_list']:
            available_categories[ev.category.id] = True
            
        for cat in categories:
            if cat.id in available_categories:
                cat.available = True
            else:
                cat.available = False

        context['categories'] = categories


        # override these in base classes
        context['next_desc'] = "Next"
        context['prev_desc'] = "Prev"

        context.update(self.get_extra_context_data(start_date, end_date))
        return context

class WeekView(PeriodView):
    days = 7
    url_name = 'week'

    def get_extra_context_data(self, start_date, end_date):
        context = {}

        title = "Week {0}/{1} &ndash; {2}/{3}".format(start_date.day, start_date.month, end_date.day, end_date.month)
        context['title'] = safestring.mark_safe(title)

        context['next_desc'] = "Next week"
        context['prev_desc'] = "Previous week"

        return context

class DayView(PeriodView):
    days = 1
    url_name = 'day'

    def get_extra_context_data(self, start_date, end_date):
        context = {}

        context['title'] = date2str(start_date, short=False)
        context['next_desc'] = date2str(start_date + timedelta(days=1))
        context['prev_desc'] = date2str(start_date - timedelta(days=1))

        return context

class EventDetailView(generic.DetailView):
    model = Event
    template_name = "events/event_detail.html"

class VenueListView(generic.ListView):
    model = Venue
    template_name = "events/venue_list.html"

class VenueDetailView(generic.DetailView):
    model = Venue
    template_name = "events/venue_detail.html"

    def get_context_data(self, **kwargs):
        context = super(VenueDetailView, self).get_context_data(**kwargs)
        context['upcoming_events'] = queries.UpcomingEvents(venue = self.object)[0:10]
        for ev in context['upcoming_events']:
            ev.set_occurrence_range(start_date=date.today())

        context['recent_events'] = queries.RecentEvents(venue = self.object)[0:10]
        for ev in context['recent_events']:
            ev.set_occurrence_range(end_date=date.today() - timedelta(days=1))

        return context

# Batch add handling
# Arguably a raw JSON upload field is not the right way to accomplish this
# Particularly not with validation performed by uncaught exceptions from the model layer
# But it'll do for now
class BatchAddForm(forms.Form):
    event_data = forms.CharField(widget=forms.Textarea)

    def perform_insert(self):
        scraped_events = json.loads(self.cleaned_data['event_data'])
        added = 0
        updated = 0
        duplicates = 0

        with transaction.commit_on_success():
            for ev_spec in scraped_events:
                result = Event.add_from_json(ev_spec)
                if result == 'added':
                    added += 1
                elif result == 'updated':
                    updated += 1
                elif result == 'duplicate':
                    duplicates += 1

        return (added,updated,duplicates)

class BatchAddView(generic.FormView):
    form_class = BatchAddForm
    template_name = 'events/batch_add.html' 
    
    def form_valid(self, form):
        added,updated,duplicates = form.perform_insert()
        content = safestring.mark_safe("""\
<h1>Success</h1>
%d new, %d updated, %d duplicates
""" % (added,updated,duplicates))
        
        return render(self.request, 'events/base.html', {'content' : content})
