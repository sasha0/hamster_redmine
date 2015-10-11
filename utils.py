# -*- coding: utf-8 -*-

import json
import sys

import requests

import configuration
from models import session, SyncLog


REDMINE_HOSTNAME = getattr(configuration, 'REDMINE_HOSTNAME', None)
REDMINE_API_KEY = getattr(configuration, 'REDMINE_API_KEY', None)
REDMINE_DEFAULT_ACTIVITY = getattr(configuration, 'REDMINE_DEFAULT_ACTIVITY', 'Development')
MERGE_TASKS = getattr(configuration, 'MERGE_TASKS', True)


def _get_data(endpoint):
    """Performing GET request to Redmine API."""
    
    headers = {'X-Redmine-API-Key': REDMINE_API_KEY}
    r = requests.get(REDMINE_HOSTNAME + endpoint, headers=headers)    
    return r


def _task_exists(task_id):
    """
    Checking if corresponding task exists in Redmine, 
    before performing synchronization.
    """
    
    r = _get_data('/issues/%s.json' % task_id)
    if r.status_code == 200:
        return True
    return False


def _fact_synced(task_id, fact_id):
    """Checking if current fact was synchronized per logs."""
    
    if session.query(SyncLog).filter_by(fact_id=fact_id, 
                                        task_id=task_id).count() == 0:
        return False
    return True


def _facts_synced(task_id, fact_ids):
    """
    Merged task might have several corresponding tasks,
    so checking if they all were synchronized.
    """
    
    if not all([_fact_synced(task_id, f) for f in fact_ids]):
        return False
    return True


def _get_time_entry_activities():
    """Fetching Redmine activities."""
    
    return _get_data('/enumerations/time_entry_activities.json').json()


def _get_time_entry_activity():
    """Determining default activity ID."""
    
    activities = _get_time_entry_activities()['time_entry_activities']
    for a in activities:
        if a['name'] == REDMINE_DEFAULT_ACTIVITY:
            return a['id']
    return


def _log_sync(task_id, fact_ids):
    """Adding entry to sychronization log model."""
    
    entries = [SyncLog(fact_id=fact_id, task_id=task_id) for fact_id in fact_ids]
    session.add_all(entries)    
    session.commit()


def _sync_task(task_id, fact_ids, activity_id, duration, date):
    """Synchronizing fact by adding new time entry though Redmine API."""
    
    headers = {'X-Redmine-API-Key': REDMINE_API_KEY, 'content-type': 'application/json'}
    data = {'time_entry': {
                'issue_id': int(task_id),
                'spent_on': date.isoformat(),
                'hours': duration,
                'activity_id': activity_id,
                }
            }
    if not _facts_synced(task_id, fact_ids):
        sys.stdout.write('Logging task %s.\n' % task_id)
        r = requests.post(REDMINE_HOSTNAME + '/time_entries.json', headers=headers, data=json.dumps(data))
        if r.status_code == 201:
            _log_sync(task_id, fact_ids)


def _merge_tasks(tasks):
    """Aggregating tasks data."""
    
    for k, v in tasks.items():
        task_data = []
        task_ids = set([t['task_id'] for t in v])
        for task_id in task_ids:
            duration = 0
            fact_ids = []
            for e in v:
                if e['task_id'] == task_id:
                    duration += round(e['duration'], 1)    # summarize all time, spent on a same task
                    fact_ids.append(e['fact_id'])
            task_data.append({'fact_ids': fact_ids, 'duration': round(duration, 1), 'task_id': task_id})
        tasks[k] = task_data
    return tasks


def synchronize_tasks(tasks):
    """Performing synchronization for given bunch of facts."""
    
    if MERGE_TASKS:
        tasks = _merge_tasks(tasks)
    activity_id = _get_time_entry_activity()
    for k, v in sorted(tasks.items()):
        for e in v:
            if _task_exists(e['task_id']):
                _sync_task(e['task_id'], e['fact_ids'], activity_id, e['duration'], k)
            else:
                sys.stderr.write('Task %s does not exist in Redmine.\n' % e['task_id'])


def check_tasks(tasks):
    """Checking if given facts are already synchronized."""
    
    for k, v in sorted(tasks.items()):
        sys.stdout.write('Tasks logged on: %s\n' % k.isoformat())
        for task in v:
            if not _fact_synced(task['task_id'], task['fact_id']):
                sys.stdout.write('Task %s, fact id %s was not synchronized.\n' % (task['task_id'], task['fact_id']))
            else:
                sys.stdout.write('Task %s, fact id %s was synchronized.\n' % (task['task_id'], task['fact_id']))
