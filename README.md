#Schedule scraper for IRE conferences

This is a command-line Python program that will generate a convenient CSV of the schedules for the annual conferences held by [Investigative Reporters and Editors](http://www.ire.org/).

This [CSV of the schedule for the IRE 2015 conference in Philadelphia](https://github.com/tommeagher/irescraper/blob/master/ire2015sched.csv) was generated with the script.

The script also generates [a version of the CSV](https://github.com/tommeagher/irescraper/blob/master/GCAL_ire2015sched.csv) that is easy to import into your Google Calendar.

Schedules for previous conferences are stored in the aptly named ```pastyears/``` dir.

If you want to run this program on your own machine, here's how to do it.

##Getting started

I use [virtualenv](https://virtualenv.pypa.io/en/latest/) and [virtualenvwrapper](https://virtualenvwrapper.readthedocs.org/en/latest/) to manage my Python environments. If you use something else, adjust the instructions accordingly.

```
git clone git@github.com:tommeagher/irescraper.git   #clone the repo from Github
cd irescraper
mkvirtualenv ire   #make and activate your virtual environment
pip install -r requirements.txt   #install the dependencies
```

##Running the command-line script
It's as easy to run as ```python sched.py```. Without specifying which conference you want (either NICAR or IRE), this will look for the schedule page for the current year's NICAR by default and save it to a CSV called nicar2015sched.csv.

If you want the schedule for the organization's other marquee event--IRE--then try ```python sched.py ire```.

There are a few other optional command-line arguments as well: 

``` 
 
  -h, --help  show this help message and exit
  -g          Create a CSV in a Gcal-friendly format.
  -u URL      Pass in a different URL to scrape from the standard pattern.
  -y YEAR     Perhaps you want a previous year?
```

If you want instructions on how to get the Gcal version into your Google Calendar, [read these handy instructions](https://github.com/tommeagher/irescraper/blob/master/GCAL_README.md). 

##Contributors

* Tom Meagher
* Chris L. Keller

##Etc.
If you spot a bug, have questions or ideas for improvement, please [file a ticket](https://github.com/tommeagher/irescraper/issues) or [ping me on Twitter](http://www.twitter.com/ultracasual/).