"""Mock operational tools the agent can call, simulating internal DoctoBook-style APIs.

These are stand-ins for real internal services (appointment scheduling, practitioner
directory) and let the agent demonstrate tool calling / MCP-style behavior on top of RAG.
"""
import random
from datetime import datetime, timedelta

_MOCK_APPOINTMENTS = {
    "APT-1001": {"patient": "J. Martin", "practitioner": "Dr. Dupont", "status": "confirmed",
                 "time": "2026-07-10 09:30"},
    "APT-1002": {"patient": "S. Leroy", "practitioner": "Dr. Bernard", "status": "cancelled",
                 "time": "2026-07-09 14:00"},
    "APT-1003": {"patient": "A. Petit", "practitioner": "Dr. Dupont", "status": "completed",
                 "time": "2026-07-08 11:15"},
}

_MOCK_PRACTITIONERS = ["Dr. Dupont", "Dr. Bernard", "Dr. Moreau"]


def check_appointment_status(appointment_id: str) -> dict:
    appointment = _MOCK_APPOINTMENTS.get(appointment_id.upper())
    if not appointment:
        return {"error": f"No appointment found with id {appointment_id}"}
    return {"appointment_id": appointment_id.upper(), **appointment}


def find_practitioner_availability(practitioner_name: str, days_ahead: int = 3) -> dict:
    matches = [p for p in _MOCK_PRACTITIONERS if practitioner_name.lower() in p.lower()]
    if not matches:
        return {"error": f"No practitioner found matching '{practitioner_name}'"}

    base = datetime.now()
    slots = [
        (base + timedelta(days=random.randint(0, days_ahead), hours=random.randint(8, 17)))
        .strftime("%Y-%m-%d %H:00")
        for _ in range(3)
    ]
    return {"practitioner": matches[0], "available_slots": sorted(slots)}


TOOL_REGISTRY = {
    "check_appointment_status": {
        "function": check_appointment_status,
        "description": "Look up the status, patient, practitioner and time of an appointment by its ID (e.g. APT-1001).",
        "parameters": {"appointment_id": "string"},
    },
    "find_practitioner_availability": {
        "function": find_practitioner_availability,
        "description": "Find upcoming available time slots for a practitioner by name.",
        "parameters": {"practitioner_name": "string", "days_ahead": "int (optional)"},
    },
}
