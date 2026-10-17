import unittest
from unittest.mock import patch

import mysql.connector
from db_setup import DbQuery


class DbQueryTests(unittest.TestCase):
    @patch("db_setup.mysql.connector.connect")
    def test_connection_failure_preserves_original_error(self, connect):
        error = mysql.connector.Error("Unknown MySQL server host", errno=2005)
        connect.side_effect = error
        with self.assertRaises(mysql.connector.Error) as raised:
            DbQuery().quryexcute("SELECT 1", ())
        self.assertIs(error, raised.exception)

    @patch("db_setup.mysql.connector.connect")
    def test_cursor_creation_failure_closes_connection(self, connect):
        connection = connect.return_value
        error = mysql.connector.Error("Cursor unavailable")
        connection.cursor.side_effect = error
        with self.assertRaises(mysql.connector.Error) as raised:
            DbQuery().quryexcute("SELECT 1", ())
        self.assertIs(error, raised.exception)
        connection.rollback.assert_called_once()
        connection.close.assert_called_once()

    @patch("db_setup.mysql.connector.connect")
    def test_query_failure_survives_rollback_and_cleanup_failures(self, connect):
        connection = connect.return_value
        cursor = connection.cursor.return_value
        error = mysql.connector.Error("Query failed")
        cursor.execute.side_effect = error
        connection.rollback.side_effect = mysql.connector.Error("Connection lost")
        cursor.close.side_effect = mysql.connector.Error("Cursor lost")
        connection.close.side_effect = mysql.connector.Error("Close failed")
        with self.assertRaises(mysql.connector.Error) as raised:
            DbQuery().quryexcute("SELECT 1", ())
        self.assertIs(error, raised.exception)
        connection.close.assert_called_once()

    @patch("db_setup.mysql.connector.connect")
    def test_success_returns_rows_and_commits(self, connect):
        connection = connect.return_value
        cursor = connection.cursor.return_value
        cursor.fetchall.return_value = [(1,)]
        self.assertEqual([(1,)], DbQuery().quryexcute("SELECT %s", (1,)))
        cursor.execute.assert_called_once_with("SELECT %s", (1,))
        connection.commit.assert_called_once()
        connection.rollback.assert_not_called()
        cursor.close.assert_called_once()
        connection.close.assert_called_once()
