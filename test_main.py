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
from unittest.mock import patch
from main import (
    create_tickets,
    # get_attendee_tickets,
    # reserve_tickets,
    # release_held_tickets,
    # purchase_tickets,
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


if __name__ == "__main__":
    unittest.main()
