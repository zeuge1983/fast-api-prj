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

class Customer(BaseModel):
    id: int
    name: str
    email: str

class TicketDetail(BaseModel):
    id: int
    title: str
    status: str
    priority: str
    category: str
    description: str
    customer: Customer

    @classmethod
    def from_row(cls, row):
        """Build the detail response from a raw CSV row (pandas dict)."""
        return cls(
            id=int(row["ticket_id"]),
            title=str(row["title"]),
            status=str(row["status"]),
            priority=str(row["priority"]),
            category=str(row["category"]),
            description=str(row["description"]),
            customer=Customer(
                id=int(row["customer_id"]),
                name=str(row["customer_name"]),
                email=str(row["customer_email"]),
            ),
        )
