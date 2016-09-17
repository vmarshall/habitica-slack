from django.core.urlresolvers import resolve
from django.test import TestCase


class UrlsTestCase(TestCase):
    def test_sync_message_to_habitica_url(self):
        # act
        resolver = resolve('/sync_message_to_habitica')

        # assert
        self.assertEquals(resolver.view_name, 'habitica_slack.views.sync_message_to_habitica')

    def test_sync_messages_to_slack_url(self):
        # act
        resolver = resolve('/sync_messages_to_slack')

        # assert
        self.assertEquals(resolver.view_name, 'habitica_slack.views.sync_messages_to_slack')