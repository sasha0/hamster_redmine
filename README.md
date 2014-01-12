# Hamster-redmine

Hamster-redmine is a simple command-line script, which helps to synchronize tracked time from [Hamster](http://projecthamster.wordpress.com/) time tracker to [Redmine](http://www.redmine.org/) project management application. Script heavily uses hamster's API and for now needs to run from same user as hamster-indicator.

# Configuration

`REDMINE_HOSTNAME` — URL of your Redmine instance

`REDMINE_API_KEY` — your personal API key, available in **My account** section

`REDMINE_DEFAULT_ACTIVITY` - title of activity, you'd like to use for synchronization.

# Usage

By default, script checks logs for existing time entry - so if it exists, no need to synchronize it once more.

For instance, you can check if all of your weekly tasks are synchronized with Redmine:  

```bash
python hamster-indicator -w
```

Or you can synchronize all time entries later September 1, 2013:

```bash
python hamster-indicator -f 2013-09-01 -s
```
