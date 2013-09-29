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
                print "Yes"
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
    default_venue = forms.ModelChoiceField(
        queryset = Venue.objects,
        required=False, 
        help_text='Used if no venue specified for an event. If all events have venues specified this field is not required',
    )

    default_category = forms.ModelChoiceField(
        queryset = Category.objects,
        required=False,
        help_text='Used if no category specified for an event. If all events have categories specified this field is not required',
    )
    
    event_data = forms.CharField(widget=forms.Textarea)

    def perform_insert(self):
        scraped_events = json.loads(self.cleaned_data['event_data'])
        num_events = 0

        for ev_spec in scraped_events:
            # FIXME: most of this should be done in Event.from_json()/Occurrence.from_json()
            # FIXME: assumes the uploaded JSON was a valid event description...
            ev = Event(name=ev_spec['name'], description=ev_spec['description'])

            # optional fields
            if 'website' in ev_spec: ev.website = ev_spec['website']
            if 'ticket_details' in ev_spec: ev.ticket_details = ev_spec['ticket_details']
            if 'ticket_website' in ev_spec: ev.ticket_website = ev_spec['ticket_website']

            # Set venue and category. If they were specified (as strings) in the JSON upload
            # find the record in the database. If we're using the default optionally specified
            # by the user we already have the ORM object since we use a ModelChoiceField.
            if 'venue' in ev_spec:
                try:
                    ev.venue = Venue.objects.get(name=ev_spec['venue'])
                except:
                    return "<h1>error</h1><p>Could not find venue '%s' in database" % ev_spec['venue']
            else:
                if self.cleaned_data['default_venue'] is None:
                    return "<h1>error</h1><p>Error processing event '%s': no venue specified and no default venue set.</p>" % ev.name
                else:
                    ev.venue = self.cleaned_data['default_venue']

            if 'category' in ev_spec:
                try:
                    ev.category = Category.objects.get(name=ev_spec['category'])
                except:
                    return "<h1>error</h1><p>Could not find category '%s' in database" % ev_spec['category']
            else:
                if self.cleaned_data['default_category'] is None:
                    return "<h1>error</h1><p>Error processing event '%s': no category specified and no default category set.</p>" % ev.name
                else:
                    ev.category = self.cleaned_data['default_category']

            ev.save()

            # Process occurrences
            for occ_spec in ev_spec['occurrences']:
                occ = Occurrence()
                occ.start_date = datetime.strptime(occ_spec['start_date'], "%Y-%m-%d").date()
                if 'start_time' in occ_spec: occ.start_time = datetime.strptime(occ_spec['start_time'], "%H:%M").time()
                if 'end_date' in occ_spec: occ.end_date = datetime.strptime(occ_spec['end_date'], "%Y-%m-%d").date()
                if 'end_time' in occ_spec: occ.end_time = datetime.strptime(occ_spec['end_time'], "%H:%M").time()
                ev.occurrence_set.add(occ)

            num_events += 1

        return "<h1>Success!</h1><p>Added %d events.</p>" % (num_events)

class BatchAddView(generic.FormView):
    form_class = BatchAddForm
    template_name = 'events/batch_add.html' 
    
    def form_valid(self, form):
        content = safestring.mark_safe(form.perform_insert())
        return render(self.request, 'events/base.html', {'content' : content})

