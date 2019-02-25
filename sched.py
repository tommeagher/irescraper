#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
from datetime import date, datetime, timedelta

import requests
from lxml import html
import unicodecsv

class Conference:
    def __init__(self, conf='NICAR', year=None):
        self.conf = conf
        if year:
            self.year=int(year)
        else:
            self.year = date.today().year
        self.output_file = "{0}{1}sched.csv".format(conf.lower(), self.year)
        self.schedule = []
        
    def sniff_url(self):
        '''
        Try to guess the URL based on how IRE has done it in the past.
        '''
        self.url = 'http://ire.org/events-and-training/conferences/{0}-{1}/schedule/'.format(self.conf.lower(), self.year)
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
        r=requests.get(self.url, headers=headers)
        if not r.ok:
            self.url = 'http://ire.org/events-and-training/conferences/{0}{1}/schedule/'.format(self.conf.lower(), self.year)
            s = requests.get(self.url, headers=headers)
            if not s.ok:
                self.url = 'http://ire.org/events-and-training/conferences/{0}{1}/schedule/'.format(self.conf.lower(), str(self.year)[-2:])
                print(self.url)
                t = requests.get(self.url, headers=headers)
                if not t.ok:
                    print "Unable to guess URL. Please specify a URL to scrape with the -u flag."
                    exit()
                else:
                    self.url_content = t.content
            else:
                self.url_content = s.content
        else:
            self.url_content = r.content

    def update_url(self, url):
        '''
        Update the URL if a user passes in a command-line argument specifying a non-default URL.
        '''
        self.url = url

    def add(self, session):
        '''
        Add a session object to the conference schedule.
        '''
        self.schedule.append(session)

    def dateify(self, date_string):
        '''
        Take an IRE date string and make it a Python date object
        '''
        try:
            conf_date = datetime.strptime(date_string, "%a., %B %d")
            first_day = date(self.year, conf_date.month, conf_date.day)
        except ValueError:
            conf_date = datetime.strptime(date_string, "%a., %b. %d")
            first_day = date(self.year, conf_date.month, conf_date.day)
        self.conf_date = first_day
        return self.conf_date

    def scrape(self):
        '''
        Scrape each item on the schedule into a Session instance
        '''
        try: 
            if self.url_content:
                conf_html = self.url_content
        except:
            headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
            r = requests.get(self.url, headers=headers)
            if not r.ok:
                print "Invalid URL. Please specify a valid URL to scrape with the -u flag."
                exit()
            else:
                conf_html = r.content
        #cheat to drop pesky curly apostrophes
        conf_html = conf_html.replace('&rsquo;', "'")
        tree = html.fromstring(conf_html)
        first_day = tree.xpath('body/main/div/div/div/div/section[2]/article/div/ul[1]/li[1]/a')[0].text
        self.dateify(first_day)

        
        days = tree.find_class('list-table-1 schedule-list blank-list pane')
        datediff = timedelta(days=1)
        date = self.conf_date

        day_counter = 0

        for day in days:
            sessions = day.xpath('li')

            for session in sessions:
                item = Session()
                anchor = session.xpath('div/h3/a')[0]
                item.url = 'http://ire.org'+ anchor.values()[0]

                iteminfo = session.xpath(".//div[contains(@class, 'event-content') and contains(@class, 'item-content')]")[0]

                if len(iteminfo.find_class("event-speakers")) > 0:
                    item.speaker = iteminfo.find_class("event-speakers")[0].text_content().strip().split(':')[1].strip()
                else: item.speaker = ""

                desc_chunk = iteminfo.xpath('.//p[not(@class)]')
                new_desc = ''
                for p in desc_chunk:
                    if len(p.text_content().strip()) > 0:
                        # remove blocks of spaces that result from links in text
                        desc_block = ' '.join(p.text_content().split())

                        new_desc = new_desc + desc_block.strip() + '\n'


                item.desc = new_desc

                item.name = iteminfo.xpath(".//h3[contains(@class, 'event-title') and contains(@class, 'item-title') and contains(@class, 'title')]")[0].text_content().strip()

                item.topic = item.tagging(item.name)
                item.session_date = date

                space_time = session.xpath(".//div[contains(@class, 'event-meta') and contains(@class, 'item-meta')]")[0]
                item.place = space_time.find_class('event-location')[0].text_content().strip()
                times = space_time.xpath('p')[0].text_content().strip()
                start_time = times.split('-')[0].strip()
                if len(start_time.split()[0])<=2:
                    item.start_time = start_time.split()[0]+":00 " + start_time.split()[1]
                else:
                    item.start_time = start_time
                end_time = times.split('-')[1].strip()
                if len(end_time.split()[0])<=2:
                    item.end_time = end_time.split()[0]+":00 " + end_time.split()[1]
                else:
                    item.end_time = end_time
                
                self.add(item)

            date += datediff
            day_counter+=1
        self.day_counter = day_counter

    def write(self, gcal=None):
        '''
        Write all the Session instances in this Conference instance to a CSV
        '''
        if gcal:
            self.output_file = 'GCAL_'+self.output_file
        else:
            self.output_file = self.output_file
            
        with open(self.output_file, 'wb') as f:
            headers = ['Topic', 'Subject', 'Start Date', 'Start Time', 'End Date', 'End Time']
            if gcal:
                headers.extend(['All Day Event', 'Description', 'Location', 'Private'])
            else:
                headers.extend(['Speaker(s)', 'Description', 'Location', 'URL'])
            w = unicodecsv.writer(f, encoding='utf-8')
            w.writerow(headers)

            for session in self.schedule:
                output_row=[session.topic, session.name, session.session_date, session.start_time, session.session_date, session.end_time]

                if gcal:
                    if session.speaker=='TBA' or session.speaker == '':
                        desc = session.desc
                    else:
                        desc = session.speaker + ' - ' + session.desc + ' | URL: ' + session.url
                    output_row.extend([session.allday, desc, session.place, session.private])
                else:
                    output_row.extend([session.speaker, session.desc, session.place, session.url])

                w.writerow(output_row)

class Session:
    def __init__(self):
        self.allday = False
        self.private = False
        self.tags = ''

    def tagging(self, name):
        '''
        Simple session tagging on major CAR/dev topics.
        '''
        session_topics = [
            {"tag": "python", "terms": ["pycar", "python", "django", "first news app"]},
            {"tag": "ruby", "terms": ["ruby"]},
            #{"tag": "r", "terms": ["First steps with R", "Visualizing your data with R", "R: Preplication"]},
            {"tag": "databases", "terms": ["sqlite", "mysql", "sql"]},
            {"tag": "maps", "terms": ["qgis", "fusion tables", "ArcGIS", "Mapbox", "CartoDB", "Leaflet"]},
            {"tag": "tableau", "terms": ["tableau"]},
            {"tag": "statistics", "terms": ["statistics", "stats"]},
            {"tag": "spreadsheets", "terms": ["excel", "access", "openrefine", "PDFs"]},
            {"tag": "javascript", "terms": ["javascript", "d3"]},
            {"tag": "regex", "terms": ["regular expressions"]},
            {"tag": "command line", "terms": ["command line"]},
            {"tag": "web development", "terms": ["programming", "plotly", "github", "web programming", "mobile-ready", "web inspector", "grunt"]},
        ]

        name_lower = name.lower()

        matched_topics = []

        for topic in session_topics:
            if any(word in name_lower for word in topic["terms"]):
                matched_topics.append(topic["tag"])

        if matched_topics > 0:
            output = ", ".join(matched_topics)
            self.tags = output
            return self.tags

def main():
    '''
    Collect the command line arguments and run the scrapers.
    '''
    parser = argparse.ArgumentParser(description="Scrape IRE/NICAR schedules into CSVs")
    parser.add_argument('conf', default='NICAR', nargs='?', help='What conference do you want a schedule for? IRE or NICAR?')
    parser.add_argument('-g', dest='gcal', action='store_true', help='Create a CSV in a Gcal-friendly format.')
    parser.add_argument('-u', dest='url', help='Pass in a different URL to scrape from the standard pattern.')
    parser.add_argument('-y', dest='year', help='Perhaps you want a previous year?')

    args = parser.parse_args()

    if args.year:
        conf = Conference(args.conf, year=args.year)
    else:
        conf = Conference(args.conf)

    if args.url:
        conf.update_url(args.url)
    else:
        print "Sussing out the URL"
        conf.sniff_url()

    print "Requesting {0}".format(conf.url)

    print "Scraping {0} schedule...".format(conf.conf.upper())

    conf.scrape()

    if args.gcal:
        conf.write(gcal=True)
    else:
        conf.write(gcal=None)

    print "Found {0} {1} sessions over {2} days.".format(len(conf.schedule), conf.conf.upper(), conf.day_counter)
    
    print "Writing {0} schedule to {1}".format(conf.conf.upper(), conf.output_file)

    print "Have fun!"

if __name__ == '__main__':
    main()
