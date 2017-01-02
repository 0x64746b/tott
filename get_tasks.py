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


class TaskClient(object):

    def __init__(self, server, username, password, calendar):
        self._calendar = TaskClient._select_calendar(
            os.path.join(server, calendar),
            TaskClient._login(server, username, password).calendars()
        )

    @staticmethod
    def _login(server, username, password):
        return DAVClient(
            server,
            username=username,
            password=password
        ).principal()

    def retrieve_tasks(self):
        alarmable_tasks = []

        for todo in self._calendar.todos():
            data = TaskClient._parse_data(todo.data)
            if data.get('LOCATION', '').lower() == ALARM_LOCATION:
                alarmable_tasks.append(data['SUMMARY'].strip())

        return alarmable_tasks

    @staticmethod
    def _select_calendar(calendar_url, calendars):
        return [
            calendar for calendar in calendars
            if calendar.url == calendar_url
        ].pop()

    @staticmethod
    def _parse_data(data):
        return {
            key: value for key, value in
            [line.split(':') for line in data.split('\n') if line]
        }


if __name__ == '__main__':
    task_client = TaskClient(CARDDAV_ENDPOINT, USER, PASSWORD, CALENDAR_PATH)
    tasks = task_client.retrieve_tasks()

    for task in tasks:
        print(' -', task)
