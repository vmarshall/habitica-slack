import json
import os
import time
import mock

import requests_mock
from django.test import TestCase

from habitica_slack import actions


class ActionsTestCase(TestCase):
    def setUp(self):
        self.groupId = '123'
        self.apiUser = 'joe'
        self.apiKey = 'secret'
        self.slackWebhook = 'http://webhook-url.test/'

        os.environ['HABITICA_APIUSER'] = self.apiUser
        os.environ['HABITICA_APIKEY'] = self.apiKey
        os.environ['HABITICA_GROUPID'] = self.groupId
        os.environ['SLACK_WEBHOOK'] = self.slackWebhook

    def test_get_default_lastpost_timestamp(self):
        # arrange
        now_timestamp = (int(time.time()) - (60 * 60 * 24)) * 1000

        # act
        last_post_timestamp = actions.get_lastpost_timestamp()

        # assert
        self.assertEquals(last_post_timestamp, now_timestamp)

    def test_set_lastpost_timestamp(self):
        # arrange
        timestamp = 123

        # act
        actions.set_lastpost_timestamp(timestamp)

        # assert
        last_post_timestamp = actions.get_lastpost_timestamp()
        self.assertEquals(last_post_timestamp, timestamp)

    @requests_mock.mock()
    def test_send_message_to_habitica_from_user(self, m):
        # arrange
        data = {
            'user': 'Joe',
            'text': 'Hello!'
        }

        expected_headers = {
            'x-api-user': self.apiUser,
            'x-api-key': self.apiKey,
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        expected_url = 'https://habitica.com/api/v3/groups/123/chat'
        expected_body = 'message=%5BJoe+says%5D+Hello%21&groupId=123'

        m.post(requests_mock.ANY)

        # act
        actions.send_message_to_habitica(data['user'], data['text'])

        # assert
        history = m.request_history
        self.assertEquals(len(history), 1)

        request = history[0]
        self.assertEquals(request.url, expected_url)
        self.assertEquals(request.method, 'POST')
        self.assertDictContainsSubset(expected_headers, request.headers)
        self.assertEquals(request.body, expected_body)

    @requests_mock.mock()
    def test_send_message_to_habitica_from_slackbot_does_nothing(self, m):
        # arrange
        data = {
            'user': 'slackbot',
            'text': 'Hello!'
        }

        m.post(requests_mock.ANY)

        # act
        actions.send_message_to_habitica(data['user'], data['text'])

        # assert
        history = m.request_history
        self.assertEquals(len(history), 0)

    @requests_mock.mock()
    def test_get_messages_from_habitica(self, m):
        # arrange
        expected_headers = {
            'x-api-user': self.apiUser,
            'x-api-key': self.apiKey
        }

        expected_url = 'https://habitica.com/api/v3/groups/123/chat'

        m.get(requests_mock.ANY, text=json.dumps({'data': 'dummy_data'}))

        # act
        response = actions.get_messages_from_habitica()

        # assert
        history = m.request_history
        self.assertEquals(len(history), 1)

        request = history[0]
        self.assertEquals(request.url, expected_url)
        self.assertEquals(request.method, 'GET')
        self.assertDictContainsSubset(expected_headers, request.headers)
        self.assertEquals(request.body, None)
        self.assertEquals(response, 'dummy_data')

    @requests_mock.mock()
    def test_send_messages_to_slack(self, m):
        # arrange
        messages = [
            {
                'timestamp': 10,
                'text': 'hello from Joe',
                'user': 'Joe'
            },
            {
                'timestamp': 20,
                'text': 'hello from John',
                'user': 'John'
            },
            {
                'timestamp': 30,
                'text': 'hello from ADMIN'
            },
            {
                'timestamp': 40,
                'text': '[emma says] hello from Emma'
            },
            {
                'timestamp': 50,
                'text': 'hello from Emily',
                'user': 'Emily'
            }
        ]

        expected_headers = {
            'content-type': 'application/json'
        }

        expected_post_bodies = [
            {
                "attachments": [
                    {
                        "color": "good",
                        "fields": [
                            {
                                "value": "hello from Emily",
                                "title": "Emily"
                            }
                        ],
                        "fallback": "Emily: hello from Emily"
                    }
                ]
            },
            {
                "attachments": [
                    {
                        "color": "danger",
                        "fields": [
                            {
                                "value": "hello from ADMIN", "title": None
                            }
                        ],
                        "fallback": "hello from ADMIN"
                    }
                ]
            },
            {
                "attachments": [
                    {
                        "color": "good",
                        "fields": [
                            {
                                "value": "hello from John",
                                "title": "John"
                            }
                        ],
                        "fallback": "John: hello from John"
                    }
                ]
            }
        ]

        m.post(requests_mock.ANY)

        # act
        actions.send_messages_to_slack(messages, 15)

        # assert
        history = m.request_history
        len_history = len(history)
        self.assertEquals(len_history, 3)

        for i in range(len_history):
            request = history[i]
            self.assertEquals(request.url, self.slackWebhook)
            self.assertEquals(request.method, 'POST')
            self.assertDictContainsSubset(expected_headers, request.headers)
            self.assertEquals(json.loads(request.body), expected_post_bodies[i])

    def test_sync_messages_to_slack(self):
        # arrange
        expected_timestamp = 3
        expected_messages = [1, 2, 3]

        actions.get_lastpost_timestamp = mock.Mock(return_value=expected_timestamp)
        actions.get_messages_from_habitica = mock.Mock(return_value=expected_messages)
        actions.send_messages_to_slack = mock.Mock()

        # act
        actions.sync_messages_to_slack()

        # assert
        # noinspection PyUnresolvedReferences
        actions.send_messages_to_slack.assert_called_with(expected_messages, expected_timestamp)
