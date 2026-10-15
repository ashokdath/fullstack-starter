from django.http import HttpRequest
from ninja import Router, Status
from pydantic import EmailStr

from app.core.email import generate_test_email, send_email
from app.core.security import jwt_auth, require_superuser
from app.schemas import Message

router = Router(tags=["utils"])


@router.post("/test-email/", response={201: Message}, auth=jwt_auth)
def test_email(request: HttpRequest, email_to: EmailStr) -> Status[Message]:
    """
    Test emails.
    """
    require_superuser(request)
    email_data = generate_test_email(email_to=email_to)
    send_email(
        email_to=email_to,
        subject=email_data.subject,
        html_content=email_data.html_content,
    )
    return Status(201, Message(message="Test email sent"))


@router.get("/health-check/", response=bool)
def health_check(request: HttpRequest) -> bool:
    return True
