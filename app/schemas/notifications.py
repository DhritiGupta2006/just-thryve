from pydantic import BaseModel


class NotificationResponse(BaseModel):
    id: str
    title: str
    description: str
    category: str
    created_at: str
