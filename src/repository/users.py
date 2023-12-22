from libgravatar import Gravatar
from sqlalchemy.orm import Session

from src.database.models import User
from src.schemas import UserModel


async def get_user_by_email(email: str, db: Session) -> User | None:
    """
    The get_user_by_email function takes in an email and a database session,
    and returns the user associated with that email. If no such user exists, it returns None.

    :param email: str: Pass the email address of a user into the function
    :param db: Session: Pass the database session to the function
    :return: A user object, or none if the user doesn't exist
    :doc-author: Trelent
    """
    return db.query(User).filter(User.email == email).first()


async def create_user(body: UserModel, db: Session) -> User:
    """
    The create_user function creates a new user in the database.
        Args:
            body (UserModel): The UserModel object to be created.
            db (Session): The SQLAlchemy session object used for querying the database.

    :param body: UserModel: Pass in the data from the request body
    :param db: Session: Connect to the database
    :return: The new user
    :doc-author: Trelent
    """
    avatar = None
    try:
        g = Gravatar(body.email)
        avatar = g.get_image()
    except Exception as e:
        print(e)
    new_user = User(**body.model_dump(), avatar=avatar)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


async def update_token(user: User, refresh_token: str | None, db: Session) -> None:
    """
    The update_token function updates the refresh token for a user.

    :param user: User: Specify the user to update
    :param refresh_token: str | None: Specify that the refresh_token parameter is a string or none
    :param db: Session: Access the database
    :return: None
    :doc-author: Trelent
    """
    user.refresh_token = refresh_token
    db.commit()


async def update_avatar(email, url: str, db: Session) -> User:
    """
    The update_avatar function updates the avatar of a user.

    :param email: Find the user in the database
    :param url: str: avatar link
    :param db: Session: Pass the database session into the function
    :return: A user object
    :doc-author: Trelent
    """
    user = await get_user_by_email(email, db)
    user.avatar = url
    db.commit()
    return user


async def confirmed_email(email: str, db: Session) -> None:
    """
    The confirmed_email function takes in an email and a database session,
    and sets the confirmed field of the user with that email to True.


    :param email: str: Specify the email address of the user to be confirmed
    :param db: Session: Pass the database session to the function
    :return: None
    :doc-author: Trelent
    """
    user = await get_user_by_email(email, db)
    user.confirmed = True
    db.commit()


async def update_password(user: User, hashed_password: str, db: Session):
    """
    The update_password function takes in a user object, a hashed password string, and the database session.
    It then updates the user's password to be equal to the hashed_password string.
    Finally it commits this change and refreshes the database.

    :param user: User: Pass the user object to the function
    :param hashed_password: str: Pass the hashed password to the function
    :param db: Session: Access the database
    :return: The user object with the updated password
    :doc-author: Trelent
    """
    user.password = hashed_password
    db.commit()
    db.refresh(user)
