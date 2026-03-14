"""
Test custom Django commands.
"""

from unittest.mock import patch
from psycopg2 import OperationalError as Psycopg2OpError
from django.core.management import call_command
from django.db.utils import OperationalError
from django.test import SimpleTestCase


@patch("core.management.commands.wait_for_db.Command.check")
class CommandTests(SimpleTestCase):
    """Test commands."""

    def test_wait_for_db_ready(self, patched_check):
        """Test waiting for database when database is ready."""
        # Set the return value of the patched check method to True
        patched_check.return_value = True
        # Call the wait_for_db command
        call_command("wait_for_db")
        # Assert that the patched check method was called once
        patched_check.assert_called_once_with(databases=["default"])

    @patch("time.sleep")
    def test_wait_for_db_delayed(self, patched_sleep, patched_check):
        """Test waiting for database when getting OperationalError."""
        # Sideeffect of the patched check method to raise the errors
        patched_check.side_effect = (
            [OperationalError] * 2 + [Psycopg2OpError] * 3 + [True]
        )
        # Call the wait_for_db command
        call_command("wait_for_db")
        # Assert the patched mehtod
        self.assertEqual(patched_check.call_count, 6)
        patched_check.assert_called_with(databases=["default"])
