from pydantic import BaseModel
from typing import List, Optional
from enum import Enum

class Priority(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

class Ticket(BaseModel):
    ticket_id: int
    title: str
    priority: Priority
    category: str
    status: str
    description: str

class FilterRequest(BaseModel):
    tickets: List[Ticket]
    priority: Optional[str] = None
    status: Optional[str] = None
    category: Optional[str] = None

class TicketList(BaseModel):
    tickets: List[Ticket]