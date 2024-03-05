####################################################################################################
# Project Name: Motive Event Management System
# Course: COMP70025 - Software Systems Engineering
# File: ticketManager.py
# Description:
#
# Authors: James Hartley, Ankur Desai, Patrick Borman, Julius Gasson, and Vadim Dunaevskiy
# Date: 2024-02-20
# Version: 1.2
#
# Changes: Added assign_tickets_to_attendee, get_tickets_info, get_tickets_info_for_users,
#          update_tickets_redeemed_status, and delete_expired_tickets functions.
#
# Notes: Might be worth modifying functions to take a list of JSON requests - not just a single
#        ticket per request to avoid unnecessary back and forth with Supabase.
#           Need to set up app routes at the end of the file for API calls and define a
#        validate_request function once there is a standardised JSON request template.
####################################################################################################
from flask import Flask, jsonify
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime, timedelta
import pytz
import os
import functions_framework
from google.cloud import tasks_v2
import json

app = Flask(__name__)

# Create a Supabase client
load_dotenv()
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def purchase_ticket(event_id, attendee_id):
    """
    Attempts to purchase a ticket for a given event on behalf of an attendee.
    This version uses Cloud Tasks for asynchronous processing.

    Args:
        event_id (str): The unique identifier for the event.
        attendee_id (str): The unique identifier for the attendee purchasing the ticket.

    Returns:
        A tuple containing a boolean indicating success, and either a success message or an error message.
    """
    try:
        # Prepare Cloud Tasks data (payload)
        task_payload = {
            "event_id": event_id,
            "attendee_id": attendee_id,
        }

        # Get Cloud Tasks client (assuming you have configured it)
        client = tasks_v2.CloudTasksClient()

        # Get the queue name and location from environment variables
        queue_name = os.environ["CLOUD_TASKS_QUEUE"]
        location = os.environ["CLOUD_TASKS_LOCATION"]
        project_id = os.environ["GCP_PROJECT_ID"]

        # Construct the full queue path
        queue_path = client.queue_path(project_id, location, queue_name)

        # Create the Cloud Tasks task
        task = {"payload": json.dumps(task_payload).encode("utf-8")}

        try:
            response = client.create_task(request={"parent": queue_path}, task=task)
            print(f"Task created with name: {response.name}")
            # Respond to user immediately (e.g., confirmation message)
            return True, "Ticket purchase request submitted!"
        except Exception as e:
            print(f"Error creating Cloud Task: {e}")
            return False, "An error occurred. Please try again later."
    except Exception as e:
        return False, str(e)


# To be completed once all function requests standardized as with account manager:
def validate_request(request):
    """
    Placeholder for function to verify that a request will be unlikely to cause an error after
    an API call is made to Supabase to reduce wasted database connections.
    """
    return True


def create_tickets(event_id, price, n_tickets):
    """
    Creates a batch of N tickets for a specified event and inserts them into the database.

    Args:
        event_id (str): The unique identifier for the event to which the tickets belong.
        price (float): The price of each ticket in GBP.
        n_tickets (int): The number of tickets to create.

    Returns:
        A tuple containing a boolean indicating success, and either a success message or an error message.
    """
    # valid, message = validate_request(request)

    tickets_data = [
        {
            "event_id": event_id,
            "attendee_id": None,  # No attendee_id since tickets have not been bought yet
            "price": price,
            "redeemed": False,
        }
        for _ in range(n_tickets)
    ]  # Generate N tickets

    try:
        result = supabase.table("tickets").insert(tickets_data).execute()

        if result.error:
            return False, f"An error occurred while creating tickets: {result.error}"
        else:
            return (
                True,
                f"{n_tickets} tickets successfully created for event {event_id}.",
            )
    except Exception as e:
        return False, f"An exception occurred: {str(e)}"


def assign_tickets_to_attendee(ticket_ids, attendee_id):
    """
    Assigns a list of tickets to an attendee's account by adding their unique ID to each of the tickets.

    Args:
        ticket_ids (list): A list of ticket IDs to be assigned.
        attendee_id (str): The attendee's unique ID to assign the tickets to.

    Returns:
        A tuple containing a boolean indicating success, and either a success message or an error message.
    """
    # valid, message = validate_request(request)

    try:
        # Add attendee id to all tickets specified in one call to the Supabase API
        update_data = {"attendee_id": attendee_id}
        result = (
            supabase.table("tickets")
            .update(update_data)
            .in_("ticket_id", ticket_ids)
            .execute()
        )

        if result.error:
            return (
                False,
                f"An error occurred while assigning the tickets: {result.error}",
            )
        else:
            return True, f"Tickets successfully assigned to user {attendee_id}."
    except Exception as e:
        return False, f"An exception occurred: {str(e)}"


def get_tickets_info(ticket_ids, requested_attributes):
    """
    Fetches information for multiple tickets based on the requested attributes.

    Args:
        ticket_ids (list of str): A list of unique identifiers for the tickets.
        requested_attributes (dict): A dictionary where keys are attribute names (e.g., 'price', 'redeemed')
        and values are booleans indicating whether that attribute should be returned.

    Returns:
        A tuple containing a boolean indicating success, and either the list of ticket data or an error message.
    """
    # valid, message = validate_request(request)

    # Filter the requested attributes to include only those marked as True
    attributes_to_fetch = [
        attr for attr, include in requested_attributes.items() if include
    ]

    # Ensure that we always include 'ticket_id' for identification, if not already included
    if "ticket_id" not in attributes_to_fetch:
        attributes_to_fetch.append("ticket_id")

    # Construct the select query based on the filtered attributes
    select_query = ", ".join(attributes_to_fetch)

    try:
        result = (
            supabase.table("tickets")
            .select(select_query)
            .in_("ticket_id", ticket_ids)
            .execute()
        )

        if result.error:
            return (
                False,
                f"An error occurred while fetching ticket info: {result.error}",
            )
        elif len(result.data) == 0:
            return False, "No tickets found with the provided IDs."
        else:
            return True, result.data  # Return the list of tickets
    except Exception as e:
        return False, f"An exception occurred: {str(e)}"


def get_tickets_info_for_users(attendee_ids, requested_attributes):
    """
    Fetches ticket information for multiple users based on the attendee_ids and requested attributes.

    Args:
        attendee_ids (list of str): A list of unique identifiers for the users (attendees).
        requested_attributes (dict): A dictionary where keys are attribute names (e.g., 'price', 'redeemed')
        and values are booleans indicating whether that attribute should be returned.

    Returns:
        A dictionary with attendee IDs as keys and a list of ticket information dictionaries as values.
    """
    # valid, message = validate_request(request)

    # Determine which attributes to fetch based on requested_attributes
    attributes_to_fetch = [
        attr for attr, include in requested_attributes.items() if include
    ]

    # Always include 'ticket_id' and 'attendee_id' for identification
    if "ticket_id" not in attributes_to_fetch:
        attributes_to_fetch.append("ticket_id")
    if "attendee_id" not in attributes_to_fetch:
        attributes_to_fetch.append("attendee_id")

    # Construct the select query
    select_query = ", ".join(attributes_to_fetch)

    try:
        # Fetch tickets for the given user IDs
        result = (
            supabase.table("tickets")
            .select(select_query)
            .in_("attendee_id", attendee_ids)
            .execute()
        )

        if result.error:
            return (
                False,
                f"An error occurred while fetching tickets for users: {result.error}",
            )

        # Organize tickets by attendee_id
        tickets_by_user = {attendee_id: [] for attendee_id in attendee_ids}
        for ticket in result.data:
            attendee_id = ticket.get("attendee_id")
            if attendee_id in tickets_by_user:
                tickets_by_user[attendee_id].append(
                    {attr: ticket[attr] for attr in attributes_to_fetch}
                )

        return True, tickets_by_user
    except Exception as e:
        return False, f"An exception occurred: {str(e)}"


def update_tickets_redeemed_status(ticket_ids, redeemed_status):
    """
    Updates the 'redeemed' status of a set of tickets.

    Args:
        ticket_ids (list of str): A list of unique identifiers for the tickets to be updated.
        redeemed_status (bool): The new redeemed status to set for the tickets.

    Returns:
        A tuple containing a boolean indicating success, and either a success message or an error message.
    """
    # valid, message = validate_request(request)

    # Prepare the data for update
    update_data = {"redeemed": redeemed_status}

    try:
        # Update the redeemed status for all specified tickets
        result = (
            supabase.table("tickets")
            .update(update_data)
            .in_("ticket_id", ticket_ids)
            .execute()
        )

        if result.error:
            return False, f"An error occurred while updating tickets: {result.error}"
        else:
            return True, "Updated redeemed status for tickets successfully."
    except Exception as e:
        return False, f"An exception occurred: {str(e)}"


# Note: Can be replaced with Supabase scheduled tasks (cron jobs) if we are happy to integrate
# further with Supabase. Cron jobs would be easier to set up but harder to migrate from.
def delete_expired_tickets(days_ago):
    """
    Deletes tickets for events that occurred a specified number of days ago or more.

    Args:
        days_ago (int): The number of days in the past to consider tickets for deletion.

    Returns:
        A tuple containing a boolean indicating success, and either a success message or an error message.
    """
    # valid, message = validate_request(request)

    # Calculate the cutoff datetime
    cutoff_date = datetime.now(pytz.utc) - timedelta(days=days_ago)

    try:
        # Fetch event_ids for events before the cutoff_date
        events_result = (
            supabase.table("events")
            .select("event_id")
            .lte("date_time", cutoff_date.isoformat())
            .execute()
        )
        if events_result.error:
            return False, f"Error fetching events: {events_result.error}"

        # Extract event_ids from the query result
        event_ids = [event["event_id"] for event in events_result.data]

        # Delete tickets linked to those event_ids
        if event_ids:
            delete_result = (
                supabase.table("tickets").delete().in_("event_id", event_ids).execute()
            )
            if delete_result.error:
                return False, f"Error deleting tickets: {delete_result.error}"

        return True, "Old tickets successfully deleted."
    except Exception as e:
        return False, f"An exception occurred: {str(e)}"


@functions_framework.http
def api_purchase_ticket(request):
    req_data = request.get_json()

    # Validate request data
    if not req_data or "event_id" not in req_data or "attendee_id" not in req_data:
        return jsonify({"error": "Invalid or missing data in JSON payload"}), 400

    # Function call
    result = purchase_ticket(req_data["event_id"], req_data["attendee_id"])

    # Handle the possible outcomes
    if not result[0]:
        return jsonify({"error": result[1]}), 500
    else:
        return jsonify({"message": result[1]}), 200


@functions_framework.http
def process_ticket_purchase(request):
    """
    This function is triggered by the Cloud Tasks queue to process ticket purchases.
    """
    # Get the task payload data
    data = json.loads(request.data.decode("utf-8"))
    event_id = data["event_id"]
    attendee_id = data["attendee_id"]

    """
  ** Your existing logic for processing the ticket purchase with Supabase goes here **
  """

    try:
        # Check for available tickets for the event
        available_tickets = (
            supabase.table("tickets")
            .select("ticket_id")
            .eq("event_id", event_id)
            .eq("status", "available")
            .limit(1)
            .execute()
        )

        if available_tickets.error or not available_tickets.data:
            return "No available tickets for this event."

        ticket_id = available_tickets.data[0]["ticket_id"]

        # Update the ticket to mark it as sold and assign the attendee_id
        update_result = (
            supabase.table("tickets")
            .update({"status": "sold", "attendee_id": attendee_id})
            .eq("ticket_id", ticket_id)
            .execute()
        )

        if update_result.error:
            return f"Failed to update ticket status: {update_result.error}"

        # Assuming successful payment and ticket update
        return "Ticket purchase successful!"

    except Exception as e:
        return f"An error occurred during purchase processing: {str(e)}"


@functions_framework.http
def api_create_tickets(request):
    req_data = request.get_json()

    # Validate request data
    if (
        not req_data
        or "event_id" not in req_data
        or "price" not in req_data
        or "n_tickets" not in req_data
    ):
        return jsonify({"error": "Invalid or missing data in JSON payload"}), 400

    # Function call
    result = create_tickets(
        req_data["event_id"], req_data["price"], req_data["n_tickets"]
    )

    # Handle the possible outcomes
    if not result[0]:
        return jsonify({"error": result[1]}), 500
    else:
        return jsonify({"message": result[1]}), 200


@functions_framework.http
def api_assign_tickets_to_attendee(request):
    req_data = request.get_json()

    # Validate request data
    if not req_data or "ticket_ids" not in req_data or "attendee_id" not in req_data:
        return jsonify({"error": "Invalid or missing data in JSON payload"}), 400

    # Function call
    result = assign_tickets_to_attendee(req_data["ticket_ids"], req_data["attendee_id"])

    # Handle the possible outcomes
    if not result[0]:
        return jsonify({"error": result[1]}), 500
    else:
        return jsonify({"message": result[1]}), 200


@functions_framework.http
def api_get_tickets_info(request):
    req_data = request.get_json()

    # Validate request data
    if (
        not req_data
        or "ticket_ids" not in req_data
        or "requested_attributes" not in req_data
    ):
        return jsonify({"error": "Invalid or missing data in JSON payload"}), 400

    # Function call
    result = get_tickets_info(req_data["ticket_ids"], req_data["requested_attributes"])

    # Handle the possible outcomes
    if not result[0]:
        return jsonify({"error": result[1]}), 500
    else:
        return jsonify({"tickets_info": result[1]}), 200


@functions_framework.http
def api_get_tickets_info_for_users(request):
    req_data = request.get_json()

    # Validate request data
    if (
        not req_data
        or "attendee_ids" not in req_data
        or "requested_attributes" not in req_data
    ):
        return jsonify({"error": "Invalid or missing data in JSON payload"}), 400

    # Function call
    result = get_tickets_info_for_users(
        req_data["attendee_ids"], req_data["requested_attributes"]
    )

    # Handle the possible outcomes
    if not result[0]:
        return jsonify({"error": result[1]}), 500
    else:
        return jsonify({"tickets_info_by_user": result[1]}), 200


@functions_framework.http
def api_update_tickets_redeemed_status(request):
    req_data = request.get_json()

    # Validate request data
    if (
        not req_data
        or "ticket_ids" not in req_data
        or "redeemed_status" not in req_data
    ):
        return jsonify({"error": "Invalid or missing data in JSON payload"}), 400

    # Function call
    result = update_tickets_redeemed_status(
        req_data["ticket_ids"], req_data["redeemed_status"]
    )

    # Handle the possible outcomes
    if not result[0]:
        return jsonify({"error": result[1]}), 500
    else:
        return jsonify({"message": result[1]}), 200


@functions_framework.http
def api_delete_expired_tickets(request):
    req_data = request.get_json()

    # Validate request data
    if not req_data or "days_ago" not in req_data:
        return jsonify({"error": "Invalid or missing data in JSON payload"}), 400

    # Function call
    result = delete_expired_tickets(req_data["days_ago"])

    # Handle the possible outcomes
    if not result[0]:
        return jsonify({"error": result[1]}), 500
    else:
        return jsonify({"message": result[1]}), 200
