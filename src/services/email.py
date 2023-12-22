from pathlib import Path

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from fastapi_mail.errors import ConnectionErrors
from pydantic import EmailStr

from src.conf.config import settings
from src.services.auth import auth_service

conf = ConnectionConfig(
    MAIL_USERNAME=settings.mail_username,
    MAIL_PASSWORD=settings.mail_password,
    MAIL_FROM=settings.mail_from,
    MAIL_PORT=settings.mail_port,
    MAIL_SERVER=settings.mail_server,
    MAIL_FROM_NAME="Rest API Aplication",
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=True,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER=Path(__file__).parent / 'templates',
)


async def send_verification_email(email: EmailStr, username: str, host: str):
    """
    The send_verification_email function sends an email to the user with a link that they can click on
    to verify their email address. The function takes in three parameters:
        1) An EmailStr object representing the user's email address. This is used as both the recipient of
           the verification message and as part of a token that will be sent to them, which will allow us
           to verify their identity when they click on it.

    :param email: EmailStr: Specify the email address of the user
    :param username: str: Get the username of the user
    :param host: str: Pass the host url to the template
    :return: The token_verification
    :doc-author: Trelent
    """
    try:
        token_verification = auth_service.create_email_token({"sub": email})
        message = MessageSchema(
            subject="Confirm your email ",
            recipients=[email],
            template_body={"host": host, "username": username, "token": token_verification},
            subtype=MessageType.html
        )

        fm = FastMail(conf)
        await fm.send_message(message, template_name="email_verify_template.html")
    except ConnectionErrors as err:
        print(err)


async def send_reset_email(email: EmailStr, username: str, host: str):
    """
    The send_reset_email function sends a password reset email to the user.
        Args:
            email (str): The user's email address.
            username (str): The username of the user requesting a password reset.
            host (str): The hostname of the server sending this request.

    :param email: EmailStr: Specify the email address of the user who is requesting a password reset
    :param username: str: Get the username of the user who is trying to reset their password
    :param host: str: Create a link to the reset password page
    :return: A coroutine object
    :doc-author: Trelent
    """
    try:
        token_verification = auth_service.create_email_token({"sub": email})
        message = MessageSchema(
            subject="Reset password ",
            recipients=[email],
            template_body={"host": host, "username": username, "token": token_verification},
            subtype=MessageType.html
        )

        fm = FastMail(conf)
        await fm.send_message(message, template_name="email_reset_template.html")
    except ConnectionErrors as err:
        print(err)
