# -*- coding: utf-8 -*-

import calendar
import datetime
from optparse import OptionParser
import sys

from hamster.configuration import runtime

from utils import check_tasks, synchronize_tasks

parser = OptionParser(add_help_option=False)
parser.add_option('-t', '--today', dest='today', action='store_true')
parser.add_option('-w', '--weekly', dest='weekly', action='store_true')
parser.add_option('-m', '--monthly', dest='monthly', action='store_true')
parser.add_option('-f', '--from', dest='from_date', action='store', type='string')
parser.add_option('-u', '--until', dest='until_date', action='store', type='string')
parser.add_option('-s', '--synchronize', dest='synchronize', action='store_true')
(options, args) = parser.parse_args()

facts = []

# getting list of so called "facts" from Hamster, which correspond to tracked time in Redmine
if getattr(options, 'today', None):
    facts = runtime.storage.get_todays_facts()

if getattr(options, 'weekly'):
    t = datetime.date.today()
    date = t + datetime.timedelta(days=(0 - t.weekday()))
    end_date = t + datetime.timedelta(days=(6 - t.weekday()))
    facts = runtime.storage.get_facts(date, end_date)
    
if getattr(options, 'monthly', None):
    t = datetime.date.today()
    date = datetime.date(t.year, t.month, 1)
    end_day = calendar.monthrange(t.year, t.month)[1]
    end_date = datetime.date(t.year, t.month, end_day)
    facts = runtime.storage.get_facts(date, end_date)

if getattr(options, 'from_date', None):
    from_date = getattr(options, 'from_date', None)
    date = datetime.datetime.strptime(from_date, '%Y-%m-%d')
    end_date = datetime.date.today()
    facts = runtime.storage.get_facts(date, end_date)

if getattr(options, 'from_date', None) and getattr(options, 'until_date', None):
    from_date = getattr(options, 'from_date', None)
    till_date = getattr(options, 'until_date', None)
    date = datetime.datetime.strptime(from_date, '%Y-%m-%d')
    end_date = datetime.datetime.strptime(till_date, '%Y-%m-%d')
    facts = runtime.storage.get_facts(date, end_date)
    
if not getattr(options, 'from_date', None) and getattr(options, 'until_date', None):
    sys.stdout.write('Please provide start date option, for instance: python hamster_redmine.py -t 2013-10-20.\n')

if facts:
    tasks = {}
    for fact in facts:
        # aggregating tasks data, implying that Redmine's task ID stored in "activity" field of Hamster
        task = {'fact_id': int(fact.id), 'task_id': fact.activity,
                'duration': round(fact.delta.seconds / 3600.0, 2)}
        
        if not tasks.get(fact.date, None):
            tasks[fact.date] = [task]
        else:
            tasks[fact.date].append(task)
    
    # depends on option, synchronizing aggregated tasks data or just displaying results
    if getattr(options, 'synchronize', None):
        synchronize_tasks(tasks)
    else:
        check_tasks(tasks)
else:
    sys.stdout.write('No activity found.\n')
