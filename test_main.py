####################################################################################################
# Project Name: Motive Event Management System
# Course: COMP70025 - Software Systems Engineering
# File: testTicketManager.py
# Description: This file contains unit tests for each function in the ticketManager.py file.
#
# Authors: James Hartley, Ankur Desai, Patrick Borman, Julius Gasson, and Vadim Dunaevskiy
# Date: 2024-02-20
# Version: 1.2
#
# Changes: Added tests for assign_tickets_to_attendee, get_tickets_info, get_tickets_info_for_users,
#          update_tickets_redeemed_status, and delete_expired_tickets.
#
# Notes: Tests do not verify whether schema/request format works with actual Supabase queries - only
#        the mocked responses.
####################################################################################################
import unittest
from unittest.mock import patch, MagicMock
from main import (
    create_tickets,
    assign_tickets_to_attendee,
    get_tickets_info,
    get_tickets_info_for_users,
    update_tickets_redeemed_status,
    delete_expired_tickets,
    purchase_ticket,
)


class TestPurchaseTicket(unittest.TestCase):
    @patch("main.supabase.table")
    def test_purchase_ticket_success(self, mock_table):
        # Mock the chain of method calls for a successful ticket query and update
        mock_table().select().eq().eq().limit().execute.return_value = MagicMock(
            data=[{"ticket_id": "123"}], error=None
        )
        mock_table().update().eq().execute.return_value = MagicMock(data={}, error=None)

        success, message = purchase_ticket("event123", "attendee456")

        self.assertTrue(success)
        self.assertIn("successfully purchased", message)

    @patch("main.supabase.table")
    def test_no_available_tickets(self, mock_table):
        # Simulate no available tickets found
        mock_table().select().eq().eq().limit().execute.return_value = MagicMock(
            data=[], error=None
        )

        success, message = purchase_ticket("event123", "attendee456")

        self.assertFalse(success)
        self.assertIn("No available tickets", message)

    @patch("main.supabase.table")
    def test_update_ticket_status_failure(self, mock_table):
        # Simulate finding an available ticket but failing to update its status
        mock_table().select().eq().eq().limit().execute.return_value = MagicMock(
            data=[{"ticket_id": "123"}], error=None
        )
        mock_table().update().eq().execute.return_value = MagicMock(
            data={}, error="Update failed"
        )

        success, message = purchase_ticket("event123", "attendee456")

        self.assertFalse(success)
        self.assertIn("Failed to update ticket status", message)


class TestCreateTicketsForEvent(unittest.TestCase):
    @patch("main.supabase")
    def test_create_tickets_success(self, mock_supabase):
        mock_result = MagicMock()
        mock_result.error = None
        mock_supabase.table().insert().execute.return_value = mock_result

        event_id = "test-event-id"
        price = 10.0
        n_tickets = 5

        success, message = create_tickets(event_id, price, n_tickets)

        self.assertTrue(success)
        self.assertEqual(
            message, f"{n_tickets} tickets successfully created for event {event_id}."
        )

    @patch("main.supabase")
    def test_create_tickets_for_event_failure(self, mock_supabase):
        mock_result = MagicMock()
        mock_result.error = "Database error"
        mock_supabase.table().insert().execute.return_value = mock_result

        event_id = "test-event-id"
        price = 10.0
        n_tickets = 5

        success, message = create_tickets(event_id, price, n_tickets)

        self.assertFalse(success)
        self.assertIn("An error occurred while creating tickets", message)


class TestAssignTicketsToAttendee(unittest.TestCase):
    @patch("main.supabase")
    def test_assign_tickets_to_attendee_success(self, mock_supabase):
        # Setup mock Supabase response for a successful update operation
        mock_result = MagicMock()
        mock_result.error = None
        mock_supabase.table().update().in_().execute.return_value = mock_result

        ticket_ids = ["ticket-id-1", "ticket-id-2"]
        attendee_id = "attendee-id"

        success, message = assign_tickets_to_attendee(ticket_ids, attendee_id)

        self.assertTrue(success)
        self.assertIn("Tickets successfully assigned", message)

    @patch("main.supabase")
    def test_assign_tickets_to_attendee_failure(self, mock_supabase):
        # Setup mock Supabase response for a failed update operation
        mock_result = MagicMock()
        mock_result.error = "An error occurred"
        mock_supabase.table().update().in_().execute.return_value = mock_result

        ticket_ids = ["ticket-id-1", "ticket-id-2"]
        attendee_id = "attendee-id"

        success, message = assign_tickets_to_attendee(ticket_ids, attendee_id)

        self.assertFalse(success)
        self.assertIn("An error occurred while assigning the tickets", message)

    @patch("main.supabase")
    def test_assign_tickets_to_attendee_exception(self, mock_supabase):
        # Setup mock Supabase to raise an exception during the update operation
        mock_supabase.table().update().in_().execute.side_effect = Exception(
            "Database error"
        )

        ticket_ids = ["ticket-id-1", "ticket-id-2"]
        attendee_id = "attendee-id"

        success, message = assign_tickets_to_attendee(ticket_ids, attendee_id)

        self.assertFalse(success)
        self.assertIn("An exception occurred", message)


class TestGetTicketsInfo(unittest.TestCase):
    @patch("main.supabase")
    def test_get_tickets_info_success(self, mock_supabase):
        # Setup mock Supabase response for successful ticket info retrieval
        mock_result = MagicMock()
        mock_result.error = None
        mock_result.data = [
            {"ticket_id": "ticket-id-1", "price": 20.0, "redeemed": False},
            {"ticket_id": "ticket-id-2", "price": 25.0, "redeemed": True},
        ]
        mock_supabase.table().select().in_().execute.return_value = mock_result

        ticket_ids = ["ticket-id-1", "ticket-id-2"]
        requested_attributes = {"price": True, "redeemed": True}

        success, data = get_tickets_info(ticket_ids, requested_attributes)

        self.assertTrue(success)
        self.assertEqual(len(data), 2)  # Verify that two tickets' info was returned
        self.assertIn("ticket-id-1", [ticket["ticket_id"] for ticket in data])
        self.assertIn("ticket-id-2", [ticket["ticket_id"] for ticket in data])

    @patch("main.supabase")
    def test_get_tickets_info_failure(self, mock_supabase):
        # Setup mock Supabase response for a failed ticket info retrieval
        mock_result = MagicMock()
        mock_result.error = "Database error"
        mock_result.data = []
        mock_supabase.table().select().in_().execute.return_value = mock_result

        ticket_ids = ["ticket-id-1", "ticket-id-2"]
        requested_attributes = {"price": True, "redeemed": True}

        success, error_message = get_tickets_info(ticket_ids, requested_attributes)

        self.assertFalse(success)
        self.assertIn("An error occurred while fetching ticket info", error_message)

    @patch("main.supabase")
    def test_get_tickets_info_exception(self, mock_supabase):
        # Setup mock Supabase to raise an exception during ticket info retrieval
        mock_supabase.table().select().in_().execute.side_effect = Exception(
            "Unexpected error"
        )

        ticket_ids = ["ticket-id-1", "ticket-id-2"]
        requested_attributes = {"price": True, "redeemed": True}

        success, error_message = get_tickets_info(ticket_ids, requested_attributes)

        self.assertFalse(success)
        self.assertIn("An exception occurred", error_message)


class TestGetTicketsInfoForUsers(unittest.TestCase):
    @patch("main.supabase")
    def test_get_tickets_info_for_users_success(self, mock_supabase):
        # Mock Supabase response for successful ticket info retrieval
        mock_result = MagicMock()
        mock_result.error = None
        mock_result.data = [
            {"ticket_id": "ticket-1", "attendee_id": "user-id-1", "price": 20.0},
            {"ticket_id": "ticket-2", "attendee_id": "user-id-2", "price": 25.0},
        ]
        mock_supabase.table().select().in_().execute.return_value = mock_result

        attendee_ids = ["user-id-1", "user-id-2"]
        requested_attributes = {"price": True}

        success, data = get_tickets_info_for_users(attendee_ids, requested_attributes)

        self.assertTrue(success)
        self.assertIn("user-id-1", data)
        self.assertIn("user-id-2", data)
        self.assertEqual(data["user-id-1"][0]["price"], 20.0)
        self.assertEqual(data["user-id-2"][0]["price"], 25.0)

    @patch("main.supabase")
    def test_get_tickets_info_for_users_failure(self, mock_supabase):
        # Setup mock Supabase response for a failed ticket info retrieval
        mock_result = MagicMock()
        mock_result.error = "Database error"
        mock_result.data = []
        mock_supabase.table().select().in_().execute.return_value = mock_result

        attendee_ids = ["user-id-1", "user-id-2"]
        requested_attributes = {"price": True}

        success, error_message = get_tickets_info_for_users(
            attendee_ids, requested_attributes
        )

        self.assertFalse(success)
        self.assertIn(
            "An error occurred while fetching tickets for users", error_message
        )

    @patch("main.supabase")
    def test_get_tickets_info_for_users_exception(self, mock_supabase):
        # Setup mock Supabase to raise an exception during ticket info retrieval
        mock_supabase.table().select().in_().execute.side_effect = Exception(
            "Unexpected error"
        )

        attendee_ids = ["user-id-1", "user-id-2"]
        requested_attributes = {"price": True}

        success, error_message = get_tickets_info_for_users(
            attendee_ids, requested_attributes
        )

        self.assertFalse(success)
        self.assertIn("An exception occurred", error_message)


class TestUpdateTicketsRedeemedStatus(unittest.TestCase):
    @patch("main.supabase")
    def test_update_tickets_redeemed_status_success(self, mock_supabase):
        # Mock Supabase response for a successful update operation
        mock_result = MagicMock()
        mock_result.error = None
        mock_supabase.table().update().in_().execute.return_value = mock_result

        ticket_ids = ["ticket-1", "ticket-2"]
        redeemed_status = True

        success, message = update_tickets_redeemed_status(ticket_ids, redeemed_status)

        self.assertTrue(success)
        self.assertIn("Updated redeemed status for tickets successfully", message)

    @patch("main.supabase")
    def test_update_tickets_redeemed_status_failure(self, mock_supabase):
        # Setup mock Supabase response for a failed update operation
        mock_result = MagicMock()
        mock_result.error = "Database error"
        mock_supabase.table().update().in_().execute.return_value = mock_result

        ticket_ids = ["ticket-1", "ticket-2"]
        redeemed_status = False

        success, error_message = update_tickets_redeemed_status(
            ticket_ids, redeemed_status
        )

        self.assertFalse(success)
        self.assertIn("An error occurred while updating tickets", error_message)

    @patch("main.supabase")
    def test_update_tickets_redeemed_status_exception(self, mock_supabase):
        # Setup mock Supabase to raise an exception during the update operation
        mock_supabase.table().update().in_().execute.side_effect = Exception(
            "Unexpected error"
        )

        ticket_ids = ["ticket-1", "ticket-2"]
        redeemed_status = True

        success, error_message = update_tickets_redeemed_status(
            ticket_ids, redeemed_status
        )

        self.assertFalse(success)
        self.assertIn("An exception occurred", error_message)


class TestDeleteOldTickets(unittest.TestCase):
    @patch("main.supabase")
    def test_delete_expired_tickets_success(self, mock_supabase):
        # Mock fetching events successfully
        mock_events_result = MagicMock()
        mock_events_result.error = None
        mock_events_result.data = [{"event_id": "event-1"}, {"event_id": "event-2"}]

        # Mock successful deletion of tickets
        mock_delete_result = MagicMock()
        mock_delete_result.error = None

        # Setup mock side effects for the sequence of operations
        mock_supabase.table().select().lte().execute.return_value = mock_events_result
        mock_supabase.table().delete().in_().execute.return_value = mock_delete_result

        days_ago = 30
        success, message = delete_expired_tickets(days_ago)

        self.assertTrue(success)
        self.assertEqual(message, "Old tickets successfully deleted.")

    @patch("main.supabase")
    def test_delete_expired_tickets_fetch_error(self, mock_supabase):
        # Mock Supabase response for a failed event fetch
        mock_events_result = MagicMock()
        mock_events_result.error = "Database error fetching events"
        mock_supabase.table().select().lte().execute.return_value = mock_events_result

        days_ago = 30
        success, message = delete_expired_tickets(days_ago)

        self.assertFalse(success)
        self.assertIn("Error fetching events", message)

    @patch("main.supabase")
    def test_delete_expired_tickets_delete_error(self, mock_supabase):
        # Mock Supabase response for successful event fetch but failed ticket deletion
        mock_events_result = MagicMock()
        mock_events_result.error = None
        mock_events_result.data = [{"event_id": "event-1"}]
        # Mock failed ticket deletion
        mock_delete_result = MagicMock()
        mock_delete_result.error = "Database error deleting tickets"
        mock_supabase.table().select().lte().execute.side_effect = [
            mock_events_result,
            mock_delete_result,
        ]

        days_ago = 30
        success, message = delete_expired_tickets(days_ago)

        self.assertFalse(success)
        self.assertIn("Error deleting tickets", message)


if __name__ == "__main__":
    unittest.main()
