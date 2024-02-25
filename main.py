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
from flask import Flask
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime, timedelta
import pytz
import os

app = Flask(__name__)

# Create a Supabase client
load_dotenv()
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def purchase_ticket(event_id, attendee_id):
    """
    Attempts to purchase a ticket for a given event on behalf of an attendee. This simplified
    version does not explicitly use transactions but assumes atomic operations where possible.

    Args:
        event_id (str): The unique identifier for the event.
        attendee_id (str): The unique identifier for the attendee purchasing the ticket.

    Returns:
        A tuple containing a boolean indicating success, and either a success message or an error message.
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
            return False, "No available tickets for this event."

        ticket_id = available_tickets.data[0]["ticket_id"]

        # Update the ticket to mark it as sold and assign the attendee_id
        update_result = (
            supabase.table("tickets")
            .update({"status": "sold", "attendee_id": attendee_id})
            .eq("ticket_id", ticket_id)
            .execute()
        )

        if update_result.error:
            return False, "Failed to update ticket status."

        # Assuming successful payment and ticket update
        return (
            True,
            f"Ticket {ticket_id} successfully purchased for event {event_id} by attendee {attendee_id}.",
        )

    except Exception as e:
        return False, str(e)


# To be completed once all function requests standardised as with account manager:
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


# Set up app routes
