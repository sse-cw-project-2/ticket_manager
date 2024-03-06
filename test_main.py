####################################################################################################
# Project Name: Motive Event Management System
# Course: COMP70025 - Software Systems Engineering
# File: testTicketManager.py
# Description: This file contains unit tests for each function in the ticketManager.py file.
#
# Authors: James Hartley, Ankur Desai, Patrick Borman, Julius Gasson, and Vadim Dunaevskiy
# Date: 2024-03-06
# Version: 2.1
#
# Changes:
#
# Notes: Tests do not verify whether schema/request format works with actual Supabase queries - only
#        the mocked responses.
####################################################################################################


import unittest
from unittest.mock import patch, Mock
from main import (
    create_tickets,
    reserve_tickets,
    release_held_tickets,
    purchase_tickets,
    get_attendee_tickets,
    redeem_ticket,
)


class TestCreateTickets(unittest.TestCase):
    @patch("main.supabase")
    def test_create_single_ticket_success(self, mock_supabase):
        # Mock the Supabase response for successful ticket creation
        mock_supabase.table.return_value.insert.return_value.execute.return_value = (
            (
                "data",
                [
                    {
                        "ticket_id": "71894e02-3a00-4f80-a8d4-6b2830cfd00b",
                        "event_id": "fade9e23-9cb6-4f05-a1b5-e7d53d2a3b5f",
                        "attendee_id": None,
                        "price": 10,
                        "status": "available",
                    }
                ],
            ),
            ("count", None),
        )

        success, message = create_tickets(
            "fade9e23-9cb6-4f05-a1b5-e7d53d2a3b5f", 10.00, 1
        )
        self.assertTrue(success)
        self.assertEqual(message, "1 created successfully.")

    @patch("main.supabase")
    def test_create_multiple_tickets_success(self, mock_supabase):
        # Mock the Supabase response for successful ticket creation
        mock_supabase.table.return_value.insert.return_value.execute.return_value = (
            (
                "data",
                [
                    {
                        "ticket_id": "71894e02-3a00-4f80-a8d4-6b2830cfd00b",
                        "event_id": "fade9e23-9cb6-4f05-a1b5-e7d53d2a3b5f",
                        "attendee_id": None,
                        "price": 10,
                        "status": "available",
                    },
                    {
                        "ticket_id": "71894e02-3a00-4f80-a8d4-6b2830cfd00c",
                        "event_id": "fade9e23-9cb6-4f05-a1b5-e7d53d2a3b5f",
                        "attendee_id": None,
                        "price": 10,
                        "status": "available",
                    },
                    {
                        "ticket_id": "71894e02-3a00-4f80-a8d4-6b2830cfd00d",
                        "event_id": "fade9e23-9cb6-4f05-a1b5-e7d53d2a3b5f",
                        "attendee_id": None,
                        "price": 10,
                        "status": "available",
                    },
                ],
            ),
            ("count", None),
        )

        success, message = create_tickets(
            "fade9e23-9cb6-4f05-a1b5-e7d53d2a3b5f", 10.00, 3
        )
        self.assertTrue(success)
        self.assertEqual(message, "3 created successfully.")

    @patch("main.supabase")
    def test_create_ticket_failure(self, mock_supabase):
        # Mock the Supabase response for a failure
        mock_execute_method = (
            mock_supabase.table.return_value.insert.return_value.execute
        )
        mock_execute_method.return_value = ("data", []), ("error", "Database error")

        success, message = create_tickets("event123", 10.00, 1)
        self.assertFalse(success)
        self.assertEqual(message, "An error occurred: Database error")

    @patch("main.supabase")
    def test_create_ticket_exception(self, mock_supabase):
        # Mock an exception being raised during the ticket creation process
        mock_supabase.table.return_value.insert.return_value.execute.side_effect = (
            Exception("Connection error")
        )

        success, message = create_tickets("event123", 10.00, 1)
        self.assertFalse(success)
        self.assertEqual(message, "An exception occurred: Connection error")


class TestReserveTickets(unittest.TestCase):

    @patch("main.supabase.rpc")
    def test_reserve_tickets_success(self, mock_rpc):
        # Mocking successful reservation
        mock_rpc.return_value.execute.return_value.data = {
            "reserved_count": 5,
            "ticket_ids": ["id1", "id2", "id3", "id4", "id5"],
        }

        success, message, reserved_count, ticket_ids = reserve_tickets("event_id", 5)

        self.assertTrue(success)
        self.assertEqual(reserved_count, 5)
        self.assertEqual(len(ticket_ids), 5)
        self.assertIn("Reserved 5 tickets successfully.", message)

    @patch("main.supabase.rpc")
    def test_reserve_tickets_none_available(self, mock_rpc):
        # Mocking no tickets available for reservation
        mock_rpc.return_value.execute.return_value.data = {
            "reserved_count": 0,
            "ticket_ids": [],
        }

        success, message, reserved_count, ticket_ids = reserve_tickets("event_id", 5)

        self.assertFalse(success)
        self.assertEqual(reserved_count, 0)
        self.assertEqual(len(ticket_ids), 0)
        self.assertIn("No available tickets to reserve.", message)

    @patch("main.supabase.rpc")
    def test_reserve_tickets_exception(self, mock_rpc):
        # Mocking an exception during the call
        mock_rpc.return_value.execute.side_effect = Exception("Test Exception")

        success, message, reserved_count, ticket_ids = reserve_tickets("event_id", 5)

        self.assertFalse(success)
        self.assertIn("An exception occurred: Test Exception", message)
        self.assertEqual(reserved_count, 0)
        self.assertEqual(ticket_ids, [])


class TestReleaseHeldTickets(unittest.TestCase):

    @patch("main.supabase.table")
    def test_release_held_tickets_success(self, mock_table):
        # Setup for a successful update operation
        mock_table.return_value.update.return_value.in_.return_value.execute.return_value.data = (
            True
        )

        success, message = release_held_tickets(["ticket1", "ticket2", "ticket3"])

        self.assertTrue(success)
        self.assertIn("3 tickets set back to 'available.'", message)

    @patch("main.supabase.table")
    def test_release_held_tickets_failure(self, mock_table):
        # Create a mock response object that simulates the structure of the actual response
        mock_response = unittest.mock.Mock()
        mock_response.data = None
        mock_response.error = {"message": "Failed to update due to error"}

        # Setup the mocked chain of calls to return the mock response object
        mock_table.return_value.update.return_value.in_.return_value.execute.return_value = (
            mock_response
        )

        success, message = release_held_tickets(["ticket1", "ticket2", "ticket3"])

        self.assertFalse(success)
        self.assertIn("Failed to update due to error", message)

    @patch("main.supabase.table")
    def test_release_held_tickets_exception(self, mock_table):
        # Setup to throw an exception during the update operation
        mock_table.return_value.update.return_value.in_.return_value.execute.side_effect = Exception(
            "Test exception"
        )

        success, message = release_held_tickets(["ticket1", "ticket2", "ticket3"])

        self.assertFalse(success)
        self.assertIn("An exception occurred: Test exception", message)


class TestPurchaseTickets(unittest.TestCase):

    @patch("main.supabase.table")
    def test_purchase_tickets_success(self, mock_table):
        # Setup for a successful update operation
        mock_response = Mock()
        mock_response.data = True  # Simulate successful update operation
        mock_table.return_value.update.return_value.in_.return_value.execute.return_value = (
            mock_response
        )

        success, message = purchase_tickets(
            "attendee_id", ["ticket1", "ticket2", "ticket3"]
        )

        self.assertTrue(success)
        self.assertIn("tickets successfully purchased by attendee", message)

    @patch("main.supabase.table")
    def test_purchase_tickets_failure(self, mock_table):
        # Setup for a failed update operation due to Supabase error
        mock_response = Mock()
        mock_response.data = None
        mock_response.error = {"message": "Failed to update due to error"}
        mock_table.return_value.update.return_value.in_.return_value.execute.return_value = (
            mock_response
        )

        success, message = purchase_tickets(
            "attendee_id", ["ticket1", "ticket2", "ticket3"]
        )

        self.assertFalse(success)
        self.assertIn("Failed to update due to error", message)

    @patch("main.supabase.table")
    def test_purchase_tickets_exception(self, mock_table):
        # Setup to throw an exception during the update operation
        mock_table.return_value.update.return_value.in_.return_value.execute.side_effect = Exception(
            "Test exception"
        )

        success, message = purchase_tickets(
            "attendee_id", ["ticket1", "ticket2", "ticket3"]
        )

        self.assertFalse(success)
        self.assertIn("An exception occurred: Test exception", message)


class TestGetAttendeeTickets(unittest.TestCase):

    @patch("main.supabase.table")
    def test_get_attendee_tickets_success(self, mock_table):
        # Setup for a successful query with tickets found
        mock_response = Mock()
        mock_response.data = [
            {"ticket_id": "ticket1"},
            {"ticket_id": "ticket2"},
        ]  # Example tickets data
        mock_table.return_value.select.return_value.eq.return_value.execute.return_value = (
            mock_response
        )

        success, tickets = get_attendee_tickets("attendee_id")

        self.assertTrue(success)
        self.assertEqual(len(tickets), 2)
        self.assertIn({"ticket_id": "ticket1"}, tickets)

    @patch("main.supabase.table")
    def test_get_attendee_tickets_no_tickets_found(self, mock_table):
        # Setup for a query where no tickets are found
        mock_response = Mock()
        mock_response.data = []  # Simulate no tickets found with an empty list
        mock_response.error = None

        mock_table.return_value.select.return_value.eq.return_value.execute.return_value = (
            mock_response
        )

        success, message = get_attendee_tickets("attendee_id")

        self.assertFalse(success)
        self.assertIn("No tickets found.", message)

    @patch("main.supabase.table")
    def test_get_attendee_tickets_error(self, mock_table):
        # Setup for a query failure due to an error (simulate by setting the error attribute)
        mock_response = Mock()
        mock_response.data = None
        mock_response.error = {"message": "Database error"}
        mock_table.return_value.select.return_value.eq.return_value.execute.return_value = (
            mock_response
        )

        success, message = get_attendee_tickets("attendee_id")

        self.assertFalse(success)
        self.assertIn("Database error", message)

    @patch("main.supabase.table")
    def test_get_attendee_tickets_exception(self, mock_table):
        # Setup to throw an exception during the query operation
        mock_table.return_value.select.return_value.eq.return_value.execute.side_effect = Exception(
            "Test exception"
        )

        success, message = get_attendee_tickets("attendee_id")

        self.assertFalse(success)
        self.assertIn("An exception occurred: Test exception", message)


class TestRedeemTicket(unittest.TestCase):

    @patch("main.supabase.table")
    def test_redeem_ticket_success(self, mock_table):
        # Setup for a successful redemption
        mock_response = Mock()
        mock_response.data = True  # Simulate successful update operation
        mock_table.return_value.update.return_value.in_.return_value.execute.return_value = (
            mock_response
        )

        success, message = redeem_ticket("ticket_id")

        self.assertTrue(success)
        self.assertIn("Ticket successfully redeemed.", message)

    @patch("main.supabase.table")
    def test_redeem_ticket_failure(self, mock_table):
        # Setup for a failed redemption due to Supabase error
        mock_response = Mock()
        mock_response.data = None
        mock_response.error = {"message": "Failed to redeem ticket due to error"}
        mock_table.return_value.update.return_value.in_.return_value.execute.return_value = (
            mock_response
        )

        success, message = redeem_ticket("ticket_id")

        self.assertFalse(success)
        self.assertIn("Failed to redeem ticket due to error", message)

    @patch("main.supabase.table")
    def test_redeem_ticket_exception(self, mock_table):
        # Setup to throw an exception during the redemption process
        mock_table.return_value.update.return_value.in_.return_value.execute.side_effect = Exception(
            "Test exception"
        )

        success, message = redeem_ticket("ticket_id")

        self.assertFalse(success)
        self.assertIn("An exception occurred: Test exception", message)


if __name__ == "__main__":
    unittest.main()
