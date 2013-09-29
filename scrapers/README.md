Screenscrapers
==============

The Python scripts in this directory assist with getting event data into the database.
They can be invoked as

`scraper.py name`

This runs the scraper in the implementation file `name.py` and produces a JSON file
called `name.json`. Which can then be pasted into the text entry field in `/dailyinfo/batch-add`
(yes, I know, it's a work in progress).

Implementing a scraper
----------------------

Each implementation file must contain a function called `get_scraper()`. This returns
an instance of your scraper class, which should subclass `ScraperBase`. You must implement
the `scrape()` method, which should call `ScraperBase.add_event()` for each event it finds.

`add_event()` requires the event name, description, venue and category, plus an array containing
one or more occurrences (a dictionary containing `start_date`, `start_time`, optionally
`end_date` and `end_time` - you can generate it using `ScraperBase.occurrence()`). You can also 
supply an event website, ticket details (prices etc) and a ticketing website.

Testing
-------

Use local copies of data to avoid excessive requests to venue websites. If you're just
doing a bunch of `GET` requests, you can easily do this by using `ScraperBase.fetch()` to
perform them. This does a couple of things:

* If you run `scraper.py` with the `-s` option, it saves a local copy of each file you request
  in the `name.testdata` directory
* If you run `scraper.py` with the `-t` option, it uses the local copy from `name.testdata`
  rather than hitting the website

If you want to implement this yourself for some reason, it works like this:

* When run with `-s`, it calls `get_test_data()` instead of `scrape()`. The default
  implementation just sets `save_local_data` on the instance (which tells `fetch()` to save
  a local copy) and then calls `scrape()`, so you get a realistic sequence of requests
* When run with `-t`, it sets `use_local_data` on the instance. `fetch()` sees this and returns
  the local copy.
