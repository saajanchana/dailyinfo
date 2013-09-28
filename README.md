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

The default application configuration (dailyinfo/settings.py) uses the sqlite database backend included with Python so no database engine is required. The sqlite database is not checked in so you will need to regenerate it. In the top level directory, run

`manage.py syncdb`

and follow the prompts. This will create an empty database.

Once you have a database you can start the development server. Run

`manage.py runserver`

Then navigate to http://localhost:8000/ - you should see the front page. It will look pretty bare as there is nothing in the database - you can populate it by going to http://localhost:8000/admin/ or by running screenscrapers once they exist.
