from fastapi import (
    APIRouter,
    HTTPException,
    Depends,
    status,
    Security,
    BackgroundTasks,
    Request,
    Form,
)
from fastapi.responses import HTMLResponse
from fastapi.security import (
    OAuth2PasswordRequestForm,
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from fastapi.templating import Jinja2Templates
from pathlib import Path
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.schemas import UserModel, UserResponse, TokenModel, RequestEmail, ResetPassword
from src.repository import users as repository_users
from src.services.auth import auth_service
from src.services.email import send_verification_email, send_reset_email

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()

parent_directory = Path(__file__).parent.parent
templates_path = parent_directory / "services" / "templates"

if not templates_path.exists():
    raise FileNotFoundError(f"Templates directory not found: {templates_path}")

templates = Jinja2Templates(directory=templates_path)


@router.post(
    "/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def signup(
    body: UserModel,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    The signup function creates a new user in the database.
        It takes a UserModel object as input, which is validated by pydantic.
        If the email address already exists in the database, an HTTP 409 error is raised.
        The password field of the UserModel object is hashed
        A new user record with all fields except for password (which was hashed) are created and returned to the caller.

    :param body: UserModel: Get the data from the request body
    :param background_tasks: BackgroundTasks: Add a task to the background tasks queue
    :param request: Request: Get the base url of the application
    :param db: Session: Pass the database session to the repository
    :return: A dictionary, which returns massage about successful user creation
    :doc-author: Trelent
    """
    exist_user = await repository_users.get_user_by_email(body.email, db)
    if exist_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Account already exists"
        )
    body.password = auth_service.get_password_hash(body.password)
    new_user = await repository_users.create_user(body, db)
    background_tasks.add_task(
        send_verification_email, new_user.email, new_user.username, request.base_url
    )
    return {
        "user": new_user,
        "detail": "User successfully created. Check your email for confirmation.",
    }


@router.post("/login", response_model=TokenModel)
async def login(
    body: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    """
    The login function is used to authenticate a user.

    :param body: OAuth2PasswordRequestForm: Validate the request body
    :param db: Session: Get the database session from the dependency injection container
    :return: A jwt and a refresh token
    :doc-author: Trelent
    """
    user = await repository_users.get_user_by_email(body.username, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email"
        )
    if not user.confirmed:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Email not confirmed"
        )
    if not auth_service.verify_password(body.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password"
        )
    # Generate JWT
    access_token = await auth_service.create_access_token(data={"sub": user.email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": user.email})
    await repository_users.update_token(user, refresh_token, db)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.get("/refresh_token", response_model=TokenModel)
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db),
):
    """
    The refresh_token function is used to refresh the access token.
        The function takes in a refresh token and returns an access_token, a new refresh_token, and the type of token.
        If the user's current refresh_token does not match what was passed into this function then it will return an error.

    :param credentials: HTTPAuthorizationCredentials: Get the token from the request header
    :param db: Session: Pass the database session to the function
    :return: A dictionary with the access_token, refresh_token and token type
    :doc-author: Trelent
    """
    token = credentials.credentials
    email = await auth_service.decode_refresh_token(token)
    user = await repository_users.get_user_by_email(email, db)
    if user.refresh_token != token:
        await repository_users.update_token(user, None, db)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    access_token = await auth_service.create_access_token(data={"sub": email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": email})
    await repository_users.update_token(user, refresh_token, db)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.get("/confirmed_email/{token}")
async def confirmed_email(token: str, db: Session = Depends(get_db)):
    """
    The confirmed_email function is used to confirm a user's email address.
        It takes the token from the URL and uses it to get the user's email address.
        Then, it checks if that user exists in our database and if they have already confirmed their email.
        If not, then we update their record in our database with a confirmation of their email.

    :param token: str: Get the token from the url
    :param db: Session: Access the database
    :return: A message that the email is already confirmed or a message that the email has been confirmed
    :doc-author: Trelent
    """
    email = await auth_service.get_email_from_token(token)
    user = await repository_users.get_user_by_email(email, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error"
        )
    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    await repository_users.confirmed_email(email, db)
    return {"message": "Email confirmed"}


@router.post("/verify_by_email")
async def verify_by_email(
    body: RequestEmail,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    The verify_by_email function is used to verify a user's email address.
        It takes in the user's email address and sends them an email with a link that they can click on to confirm their account.
        The function also checks if the user has already confirmed their account, and returns an error message if so.

    :param body: RequestEmail: Get the email from the request body
    :param background_tasks: BackgroundTasks: Add a task to the background queue
    :param request: Request: Get the base url of the application
    :param db: Session: Get the database session
    :param : Get the user's email address from the database
    :return: A message to the user
    :doc-author: Trelent
    """
    user = await repository_users.get_user_by_email(body.email, db)

    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    if user:
        background_tasks.add_task(
            send_verification_email, user.email, user.username, request.base_url
        )
    return {"message": "Check your email for confirmation."}


@router.post("/forgot_password", status_code=status.HTTP_202_ACCEPTED)
async def forgot_password(
    body: RequestEmail,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    The forgot_password function is used to send a reset password email to the user.

    :param body: RequestEmail: Get the email from the request body
    :param background_tasks: BackgroundTasks: Add a task to the background tasks
    :param request: Request: Get the base url of the application
    :param db: Session: Get a database session
    :return: A message that tells the user to check their email for a reset password link
    :doc-author: Trelent
    """
    user = await repository_users.get_user_by_email(body.email, db)
    if user:
        background_tasks.add_task(
            send_reset_email, user.email, user.username, request.base_url
        )
    return {"message": "Check your email for reset password."}


@router.get("/reset_password_template/{token}", response_class=HTMLResponse)
async def reset_password_template(request: Request, db: Session = Depends(get_db)):
    """
    The reset_password_template function is used to render the reset_password.html template, which allows a user
    to change their password after they have requested a password reset. The function takes in the token that was sent
    to them via email and uses it to retrieve their email address from the database. It then uses this email address
    to find their username and display it on the page.

    :param request: Request: Get the request object
    :param db: Session: Pass the database session to the function
    :return: A html page with a form to reset the password
    :doc-author: Trelent
    """
    try:
        token = request.path_params.get("token")
        email = await auth_service.get_email_from_token(token)
        user = await repository_users.get_user_by_email(email, db)

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token"
            )

        return templates.TemplateResponse(
            "reset_password.html",
            {
                "request": request,
                "host": request.base_url,
                "username": user.username,
                "token": token,
                "email": email,
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred. Report this message to support: {e}",
        )


@router.post("/reset_password/{token}", response_model=dict)
async def reset_password(
    request: Request,
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db),
):
    """
    The reset_password function is used to reset a user's password.
        It takes in the new_password and confirm_password as form data,
        then hashes the new password and updates it in the database.

    :param request: Request: Get the token from the url
    :param new_password: str: Get the new password from the user
    :param confirm_password: str: Confirm that the user has entered their new password correctly
    :param db: Session: Get access to the database
    :return: A dictionary with message, new_password and confirm_password keys
    :doc-author: Trelent
    """

    if new_password != confirm_password:
        raise HTTPException(status_code=422, detail="Unprocessable Entity")

    try:
        token = request.path_params.get("token")
        email = await auth_service.get_email_from_token(token)

        hashed_password = auth_service.get_password_hash(new_password)
        user = await repository_users.get_user_by_email(email, db)
        await repository_users.update_password(user, hashed_password, db)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred. Report this message to support: {e}",
        )

    return {"message": "Password reset successfully"}
