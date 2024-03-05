####################################################################################################
# Project Name: Motive Event Management System
# Course: COMP70025 - Software Systems Engineering
# File: ticketManager.py
# Description:
#
# Authors: James Hartley, Ankur Desai, Patrick Borman, Julius Gasson, and Vadim Dunaevskiy
# Date: 2024-02-20
# Version: 2.1
#
# Changes: Overhauled functionality for core app.
#
####################################################################################################


from flask import Flask, jsonify
from supabase import create_client, Client
from dotenv import load_dotenv
import os
import functions_framework

app = Flask(__name__)

# Create a Supabase client
load_dotenv()
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def create_tickets(event_id, price, n_tickets=1):
    """
    Creates a batch of N tickets for a specified event and inserts them into the database.

    Args:
        event_id (str): The unique identifier for the event to which the tickets belong.
        price (float): The price of each ticket in GBP.
        n_tickets (int): The number of tickets to create.

    Returns:
        A tuple containing a boolean indicating success, and either a success message or an error message.
    """
    tickets_data = [
        {
            "event_id": event_id,
            "attendee_id": None,  # No attendee_id since tickets have not been bought yet
            "price": price,
        }
        for _ in range(n_tickets)
    ]  # Generate N tickets

    try:
        result, error = supabase.table("tickets").insert(tickets_data).execute()

        result_key, result_value = result
        error_key, error_value = error

        # Check the content of the 'result' tuple
        if result_key == "data" and result_value:
            return True, f"{n_tickets} created successfully."
        elif error_value:
            return False, f"An error occurred: {error_value}"
        else:
            return False, "Unexpected response: No data returned after insert."
    except Exception as e:
        return False, f"An exception occurred: {str(e)}"


def reserve_tickets(event_id, n_tickets=1):
    """
    Reserves a specified number of available tickets for a given event by updating their status to 'reserved'.

    Args:
        event_id (str): The unique identifier for the event.
        n_tickets (int): The number of tickets to reserve.

    Returns:
        A tuple containing a boolean indicating success, and either a list of ticket_ids reserved or an error message.
    """
    try:
        # Execute the query to find available tickets
        response = (
            supabase.table("tickets")
            .select("ticket_id")
            .eq("event_id", event_id)
            .eq("status", "available")
            .limit(n_tickets)
            .execute()
        )

        # Assuming the response object has a 'data' attribute for the data
        if not response.data or len(response.data) < n_tickets:
            return False, "Not enough available tickets to reserve."

        # Extract ticket IDs from the data
        ticket_ids = [ticket["ticket_id"] for ticket in response.data]

        # Execute the update operation
        update_response = (
            supabase.table("tickets")
            .update({"status": "reserved"})
            .in_("ticket_id", ticket_ids)
            .execute()
        )

        # Check the update operation was successful
        if not update_response.data:
            return False, "Failed to update ticket status to 'reserved'."

        return True, ticket_ids
    except Exception as e:
        return False, f"An exception occurred: {str(e)}"


def release_held_tickets(ticket_ids):
    """
    Marks a set of reserved tickets back to available, allowing attendees to buy them again.

    Args:
        attendee_id (str): The unique identifier for the attendee purchasing the tickets.
        ticket_ids (list of str): A list of ticket_ids to be marked as purchased.

    Returns:
        A tuple containing a boolean indicating success, and either a success message or an error message.
    """
    try:
        # Execute the update operation to mark tickets as purchased by setting attendee_id
        update_response = (
            supabase.table("tickets")
            .update({"status": "available"})
            .in_("ticket_id", ticket_ids)
            .execute()
        )

        # Check if the update operation was successful
        if update_response.data:
            return True, f"{len(ticket_ids)} tickets set back to 'available.'"
        else:
            # Assuming the update_response includes an 'error' attribute for errors
            error_message = (
                update_response.error.get("message", "Unknown error")
                if update_response.error
                else "Failed to update tickets."
            )
            return False, error_message
    except Exception as e:
        return False, f"An exception occurred: {str(e)}"


def purchase_tickets(attendee_id, ticket_ids):
    """
    Marks a set of tickets as purchased by setting the attendee column for those tickets to the given attendee_id.

    Args:
        attendee_id (str): The unique identifier for the attendee purchasing the tickets.
        ticket_ids (list of str): A list of ticket_ids to be marked as purchased.

    Returns:
        A tuple containing a boolean indicating success, and either a success message or an error message.
    """
    try:
        # Execute the update operation to mark tickets as purchased by setting attendee_id
        update_response = (
            supabase.table("tickets")
            .update({"attendee_id": attendee_id})
            .in_("ticket_id", ticket_ids)
            .execute()
        )

        # Check if the update operation was successful
        if update_response.data:
            return True, f"Tickets successfully purchased by attendee {attendee_id}."
        else:
            # Assuming the update_response includes an 'error' attribute for errors
            error_message = (
                update_response.error.get("message", "Unknown error")
                if update_response.error
                else "Failed to update tickets."
            )
            return False, error_message
    except Exception as e:
        return False, f"An exception occurred: {str(e)}"


def get_attendee_tickets(attendee_id):
    """
    Fetches all tickets associated with a given attendee_id.

    Args:
        attendee_id (str): The unique identifier for the attendee.

    Returns:
        A tuple containing a boolean indicating success, and either a list of tickets or an error message.
    """
    try:
        # Execute the query to find tickets for the given attendee_id
        response = (
            supabase.table("tickets")
            .select("*")
            .eq("attendee_id", attendee_id)
            .execute()
        )

        # Check if the query was successful and data was retrieved
        if response.data:
            return True, response.data
        else:
            # If no data was found or an error occurred, return an error message
            error_message = (
                response.error.get(
                    "message", "No tickets found for the given attendee ID"
                )
                if response.error
                else "No tickets found."
            )
            return False, error_message
    except Exception as e:
        return False, f"An exception occurred: {str(e)}"


@functions_framework.http
def api_create_tickets(request):
    req_data = request.get_json()

    # Check for required data before querying Supabase
    if not req_data:
        return jsonify({"error": "Missing JSON payload"}), 400
    if "identifier" not in req_data:
        return jsonify({"error": "Missing identifier: event_id in JSON payload"}), 400
    if "price" not in req_data:
        return jsonify({"error": "Missing price in JSON payload"}), 400
    if "n_tickets" not in req_data:
        return jsonify({"error": "Missing n_tickets in JSON payload"}), 400

    # Function call
    success, message = create_tickets(
        req_data["identifier"], req_data["price"], req_data["n_tickets"]
    )

    # Handle outcomes
    if success:
        return jsonify({"message": message}), 200
    else:
        return jsonify({"error": message}), 400


@functions_framework.http
def api_reserve_tickets(request):
    req_data = request.get_json()

    # Check for required data before querying Supabase
    if not req_data:
        return jsonify({"error": "Missing JSON payload"}), 400
    if "identifier" not in req_data:
        return jsonify({"error": "Missing identifier: event_id in JSON payload"}), 400
    if "n_tickets" not in req_data:
        return jsonify({"error": "Missing n_tickets in JSON payload"}), 400

    # Function call
    success, message = reserve_tickets(req_data["identifier"], req_data["n_tickets"])

    # Handle outcomes
    if success:
        return jsonify({"message": message}), 200
    else:
        return jsonify({"error": message}), 400


@functions_framework.http
def api_release_held_tickets(request):
    req_data = request.get_json()

    # Check for required data before querying Supabase
    if not req_data:
        return jsonify({"error": "Missing JSON payload"}), 400
    if "ticket_ids" not in req_data:
        return jsonify({"error": "Missing ticket_ids in JSON payload"}), 400

    # Function call
    success, message = release_held_tickets(req_data["ticket_ids"])

    # Handle outcomes
    if success:
        return jsonify({"message": message}), 200
    else:
        return jsonify({"error": message}), 400


@functions_framework.http
def api_purchase_tickets(request):
    req_data = request.get_json()

    # Check for required data before querying Supabase
    if not req_data:
        return jsonify({"error": "Missing JSON payload"}), 400
    if "ticket_ids" not in req_data:
        return jsonify({"error": "Missing ticket_ids in JSON payload"}), 400
    if not "identifier" not in req_data:
        return (
            jsonify({"error": "Missing identifier: attendee_id in JSON payload"}),
            400,
        )

    # Function call
    success, message = purchase_tickets(req_data["identifier"], req_data["ticket_ids"])

    # Handle outcomes
    if success:
        return jsonify({"message": message}), 200
    else:
        return jsonify({"error": message}), 400


@functions_framework.http
def api_get_attendee_tickets(request):
    req_data = request.get_json()

    # Check for required data before querying Supabase
    if not req_data:
        return jsonify({"error": "Missing JSON payload"}), 400
    if "identifier" not in req_data:
        return (
            jsonify({"error": "Missing identifier: attendee_id in JSON payload"}),
            400,
        )

    # Function call
    success, message = get_attendee_tickets(req_data["identifier"])

    # Handle outcomes
    if success:
        return jsonify({"message": message}), 200
    else:
        return jsonify({"error": message}), 400


# event_id = "fade9e23-9cb6-4f05-a1b5-e7d53d2a3b5f"
# attendee_id = "115637969968779593674"
# price = 10
# n_tickets = 5
#
# # First, attempt to create the tickets
# print(create_tickets(event_id, price, n_tickets))
#
# # Then, in each iteration, reserve and attempt to purchase tickets
# for i in range(5):
#     success_reserve, result_reserve = reserve_tickets(event_id, n_tickets)
#     if success_reserve:
#         # If tickets were successfully reserved, extract the ticket IDs
#         reserved_tickets = result_reserve
#
#         # Send some back
#         success_release, result_release = release_held_tickets(reserved_tickets)
#         # Attempt to purchase the reserved tickets
#         success_purchase, result_purchase = purchase_tickets(
#             attendee_id, reserved_tickets
#         )
#
#         print(
#             f"Attempt {i + 1}: Reservation: {result_reserve}, Purchase: {result_release}"
#         )
#     else:
#         print(f"Attempt {i + 1}: Reservation failed: {result_reserve}")
#
# print(get_attendee_tickets(attendee_id))
