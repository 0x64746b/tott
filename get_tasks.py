#!/usr/bin/env python
# coding: utf-8

from __future__ import absolute_import, print_function, unicode_literals

import os
import subprocess
import sys

from caldav import DAVClient
from sleekxmpp import ClientXMPP


CARDDAV_ENDPOINT = 'https://<example.net>/dav.php'
CARDDAV_USER = '<carddav_user>'
CARDDAV_PASSWORD = '<carddav_password>'
CALENDAR_PATH = 'calendars/{}/default/'.format(CARDDAV_USER)
ALARM_LOCATION = 'front door'

DOOR_JID = 'front_door@jabber.<example.net>'
DOOR_PASSWORD = '<jabber_password>'
NOTIFICATION_RECIPIENT = '<jabber_user>@jabber.<example.net>'
RECIPIENT_NETWORK_ADDRESS = '192.168.0.<xx>'


class LocationChecker(object):

    @staticmethod
    def is_present(network_address):
        with open(os.devnull, 'wb') as dev_null:
            exit_code = subprocess.call(
                ['ping', '-c1', network_address],
                stdout=dev_null
            )
        return not bool(exit_code)


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


class NotificationClient(ClientXMPP):
    def __init__(self, jid, password, recipient, tasks):
        super(NotificationClient, self).__init__(jid, password)

        self._recipient = recipient
        self._message = NotificationClient._format_message(tasks)

        self.add_event_handler('session_start', self._start)

    @staticmethod
    def _format_message(items):
        return '\n'.join([' - {}'.format(item) for item in items])

    def _start(self, event):
        self.send_presence()
        self.get_roster()

        self.send_message(mto=self._recipient, mbody=self._message)

        self.disconnect(wait=True)


if __name__ == '__main__':
    print('Checking recipient...')
    if not LocationChecker.is_present(RECIPIENT_NETWORK_ADDRESS):
        print(' nothing to do: recipient not on network')
        sys.exit()

    print('Retrieving tasks...')
    task_client = TaskClient(
        CARDDAV_ENDPOINT,
        CARDDAV_USER,
        CARDDAV_PASSWORD,
        CALENDAR_PATH
    )
    tasks = task_client.retrieve_tasks()

    jabber = NotificationClient(
        DOOR_JID,
        DOOR_PASSWORD,
        NOTIFICATION_RECIPIENT,
        tasks,
    )

    print('Sending notification...')
    if jabber.connect():
        jabber.process(block=True)
        print(' done')
    else:
        print(' unable to connect :(')
