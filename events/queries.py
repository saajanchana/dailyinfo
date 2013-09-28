from datetime import date, timedelta
import models
from misc import OrderedSetFromQuery

def QueryEvents(**kwargs):
    """
    Query of events sorted by first (or last) occurrence. Optional arguments:
      venue        limit results to venue
      start_date   start searching from this date
      end_date     stop searching at this date
      reverse      reverse sort order and sort by last occurrence
      categories   only return results matching one of of these category IDs
    """
    queryset = models.Event.objects.all()

    if 'venue' in kwargs:
        queryset = queryset.filter(venue = kwargs['venue'])

    if 'start_date' in kwargs:
        queryset = queryset.filter(occurrence__start_date__gte = kwargs['start_date'])

    if 'end_date' in kwargs:
        queryset = queryset.filter(occurrence__start_date__lte = kwargs['end_date'])

    if 'categories' in kwargs:
        if isinstance(kwargs['categories'], list):
            queryset = queryset.filter(category__id__in = kwargs['categories'])
        else:
            queryset = queryset.filter(category__id = kwargs['categories'])

    if kwargs.get('reverse', False):
        queryset = queryset.order_by('-occurrence')
    else:
        queryset = queryset.order_by('occurrence')

    return OrderedSetFromQuery(queryset)

def UpcomingEvents(**kwargs):
    """
    Utility function to query events occurring in the near future. Same arguments
    as QueryEvents, plus
      start_date    if not set, defaults to today
      days          restrict results to this long after start_date 
                    (overrides end_date if both are set)
    """
    if not 'start_date' in kwargs:
        kwargs['start_date'] = date.today()

    if 'days' in kwargs:
        kwargs['end_date'] = kwargs['start_date'] + timedelta(days=kwargs['days'] - 1)
        del kwargs['days']

    return QueryEvents(**kwargs)

def RecentEvents(**kwargs):
    """
    Utility function to query events occurring in the recent past. Same arguments
    as QueryEvents, plus

      end_date      if not set, defaults to yesterday
      days          restrict results to this long before end_date 
                    (overrides start_date if both are set)

    Results are ordered by most recent occurrence
    """
    if not 'end_date' in kwargs:
        kwargs['end_date'] = date.today() - timedelta(days=1)

    if 'days' in kwargs:
        kwargs['start_date'] = kwargs['end_date'] - timedelta(days=kwargs['days'] - 1)
        del kwargs['days']

    kwargs['reverse'] = True

    return QueryEvents(**kwargs)
