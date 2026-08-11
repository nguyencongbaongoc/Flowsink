"""Domain models describing entities (activity, student, device, session)."""

from .activity import CurrentActivity
from .device import Device, DeviceCapabilities
from .session import MonitoringSession
from .student import Student
from .violations import ViolationRecord

__all__ = [
    "CurrentActivity",
    "Device",
    "DeviceCapabilities",
    "MonitoringSession",
    "Student",
    "ViolationRecord",
]