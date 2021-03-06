Daily Info
==========

This is an events aggegator website.

Prerequisites
-------------

* [Python 2.7][python]
* [Django 1.5][django]
* [Beautiful Soup 4.3][soup] (for screenscrapers)

[python]: http://www.python.org
[django]: https://www.djangoproject.com/
[soup]: http://www.crummy.com/software/BeautifulSoup/

Setup
-----

The default application configuration (dailyinfo/settings.py) uses the sqlite database backend included with Python so no database engine is required. The sqlite database is not checked in so you will need to regenerate it.

First, set the correct path to where you want the database to reside. In `dailyinfo/settings.py`, edit the line

`'NAME': 'C:/Users/Saajan/Documents/GitHub/dailyinfo/sqlite3.db',`

in the `DATABASES` section. This must be an absolute path, using forward slashes as a path separator even on Windows. Now in the top level directory, run

`manage.py syncdb`

and follow the prompts. This will create an empty database. To populate the Venue and Category tables with some useful data, run

`manage.py loaddata db.json`

Once you have a database you can start the development server. Run

`manage.py runserver`

Then navigate to <http://localhost:8000/> - you should see the front page. It will look pretty bare as there no events in the database yet - you can populate it by going to <http://localhost:8000/admin/> or by running screenscrapers once they exist.

Code structure
--------------

