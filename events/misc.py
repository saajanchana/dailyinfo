# Miscellaneous utilities
from datetime import date, time, timedelta

class OrderedSetFromQuery(object):
    """
    Represents a list of query results without duplicates, ordered by first occurrence.

    Roughly emulates a SELECT DISTINCT ON query, but without forcing the query to be
    sorted by the DISTINCT field first. The QuerySet is evaluated on
     
     * iteration
     * indexing
     * __repr__

    This object supports slicing, but it's implemented entirely in Python (i.e. the
    query does not get a LIMIT or OFFSET clause) as we don't know how many rows need
    to be returned before running the query.
    """
    def __init__(self, query):
        self.query = query
        self.result = None  # underlying storage gets populated when we evaluate the query

    def __iter__(self):
        if self.result is None:
            self.result = self.OrderedSet(self.query)
        return self.result.__iter__()

    def __getitem__(self, index):
        if self.result is None:
            self.result = self.OrderedSet(self.query)
        return self.result.__getitem__(index)

    def count(self):
        if self.result is None:
            self.result = self.OrderedSet(self.query)
        return len(self.result.lst)

    def __repr__(self):
        if self.result is None:
            self.result = self.OrderedSet(self.query)
        return self.result.__repr__()

    class OrderedSet(object):
        "Implement underlying set object"
        def __init__(self, query):
            self.map = {}  # for membership testing
            self.lst = []  # storage

            for row in query:
                if not row in self.map:
                    self.map[row] = True
                    self.lst.append(row)

        def __iter__(self):
            return self.lst.__iter__()

        def __getitem__(self, index):
            return self.lst.__getitem__(index)

        def __repr__(self):
            return self.lst.__repr__()

def date2str(d, short=True):
    """
    Return date in a human readable format.

    Examples:
    Today
    Tommorow
    Yesterday
    Monday

    (if short == False)
    Tuesday, 3rd September
    Sunday, 4th January 2014

    (if short == True)
    Tue 3 Sep
    Sun 4 Jan 2014
    """
    if d == date.today():
        return "Today"
    elif d == date.today() + timedelta(days=1):
        return "Tomorrow"
    elif d == date.today() - timedelta(days=1):
        return "Yesterday"
    elif d >= date.today() and (d - date.today()) < timedelta(weeks=1):
        return "{0:%A}".format(d)
    else:
        if short:
            if d.year == date.today().year:
                return "{0:%a %d %b}".format(d)
            else:
                return "{0:%a %d %b %Y}".format(d)
        else:

            if 4 <= d.day <= 20 or 24 <= d.day <= 30:
                suffix = "th"
            else:
                suffix = {1 : "st", 2 : "nd", 3 : "rd"} [ d.day % 10 ]

            if d.year == date.today().year:
                return "{dt:%A}, {day}{suffix} {dt:%B}".format(dt=d, day=d.day, suffix=suffix)
            else:
                return "{dt:%A}, {day}{suffix} {dt:%B %Y}".format(dt=d, day=d.day, suffix=suffix)

def time2str(d):
    """
    Return time in a human readable format
    """
    if d.hour == 0:
        hour = 12
        if d.minute == 0:
            pm = " midnight"
        else:
            pm = "am"
    elif d.hour < 12:
        hour = d.hour
        pm = "am"
    elif d.hour == 12:
        hour = 12
        if d.minute == 0:
            pm = " noon"
        else:
            pm = "pm"
    else:
        hour = d.hour - 12
        pm = "pm"

    if d.minute == 0:
        return "{hour}{pm}".format(hour=hour, pm=pm)

    else:
        return "{hour}:{minute:02d}{pm}".format(hour=hour, minute=d.minute, pm=pm)
