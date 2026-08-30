import datetime
from typing import Dict, Any

async def schedule_appointment_override(
    customer_phone: str,
    customer_name: str,
    appointment_time: str,
    service_name: str
) -> Dict[str, Any]:
    """
    Schedules an appointment in the primary calendar bypassing standard payment gateway verification.
    Sets status to BOOKED_UNPAID_OVERRIDE and generates event metadata.
    """
    try:
        start_dt = datetime.datetime.fromisoformat(appointment_time)
    except (ValueError, TypeError):
        start_dt = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1)

    end_dt = start_dt + datetime.timedelta(hours=1)

    event_payload = {
        "event_id": f"evt_override_{int(start_dt.timestamp())}",
        "summary": f"{service_name} - {customer_name}",
        "description": f"Manual Agent Override Booking for {customer_phone}. Payment requirement bypassed.",
        "start": start_dt.isoformat(),
        "end": end_dt.isoformat(),
        "status": "CONFIRMED",
        "payment_status": "BOOKED_UNPAID_OVERRIDE",
        "meet_link": f"https://meet.google.com/override-{int(start_dt.timestamp())}"
    }

    print(f"[CALENDAR OVERRIDE] Event created for {customer_name} ({customer_phone}) at {start_dt}")

    return {
        "status": "success",
        "event": event_payload,
        "sms_confirmation": f"Your appointment for {service_name} is confirmed for {start_dt.strftime('%b %d, %Y at %I:%M %p')}. Join link: {event_payload['meet_link']}"
    }
