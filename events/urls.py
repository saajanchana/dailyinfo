from django.conf.urls import patterns, include, url
from django.views.generic.base import RedirectView
from django.core.urlresolvers import reverse
import views

urlpatterns = patterns('',
    # Examples:
    url(r'^$', RedirectView.as_view(url='/dailyinfo/week/')),
    url(r'^all/$', views.AllEventsView.as_view()),
    url(r'^week/(?P<start_date>\d{4}-\d{2}-\d{2})?', views.WeekView.as_view(), name='week'),
    url(r'^day/(?P<start_date>\d{4}-\d{2}-\d{2})?', views.DayView.as_view(), name='day'),
    url(r'^venue/(?P<pk>\d+)', views.VenueDetailView.as_view(), name='venue'),
    url(r'^venues/', views.VenueListView.as_view()),
    url(r'^event/(?P<pk>\d+)', views.EventDetailView.as_view(), name='event'),
    )
