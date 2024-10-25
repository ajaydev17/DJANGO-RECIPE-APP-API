"""
Test custom Django management commands.
"""

from unittest import mock
from psycopg2 import OperationalError as Psycopg2OperationalError
from django.core.management import call_command
from django.test import SimpleTestCase
from django.db.utils import OperationalError


@patch('core.management.commands.wait_for_db.Command.check')
class WaitForDbCommandTest(SimpleTestCase):
    """
    Test the wait_for_db management command.
    """

    def test_wait_for_db(self, mocked_check):
        """
        Test waiting for the database to be ready.
        """

        mocked_check.return_value = True

        call_command('wait_for_db')

        mocked_check.assert_called_once_with(databases=['default'])

    @patch('time.sleep')
    def test_wait_for_db_delay(self, mocked_sleep, mocked_check):
        """
        Test waiting for the database to be ready with a delay.
        """

        mocked_check.side_effect = [Psycopg2OperationalError] * 2 + \
                                   [OperationalError] * 3 + [True]

        call_command('wait_for_db')

        self.assertEqual(mocked_check.call_count, 6)

        mocked_check.assert_called_with(databases=['default'])