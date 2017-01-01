#!/usr/bin/env python
# coding: utf-8

from __future__ import absolute_import, print_function, unicode_literals

import os

from caldav import DAVClient


CARDDAV_ENDPOINT = 'https://<example.net>/dav.php'
USER = '<user>'
PASSWORD = '<passwd>'
CALENDAR_PATH = 'calendars/{}/default/'.format(USER)
ALARM_LOCATION = 'front door'


def _login(server, user, password):
    client = DAVClient(server, username=user, password=password)
    return client.principal()


def _retrieve_tasks(user):
    alarmable_tasks = []

    calendar = _select_calendar(user.calendars())
    for todo in calendar.todos():
        data = _parse_data(todo.data)
        if data.get('LOCATION', '').lower() == ALARM_LOCATION:
            alarmable_tasks.append(data['SUMMARY'].strip())

    return alarmable_tasks


def _select_calendar(calendars):
    return [
        calendar for calendar in calendars
        if calendar.url == os.path.join(CARDDAV_ENDPOINT, CALENDAR_PATH)
    ].pop()


def _parse_data(data):
    return {
        key: value for key, value in
        [line.split(':') for line in data.split('\n') if line]
    }


if __name__ == '__main__':
    user = _login(CARDDAV_ENDPOINT, USER, PASSWORD)
    tasks = _retrieve_tasks(user)

    for task in tasks:
        print(' -', task)

