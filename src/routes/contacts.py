from typing import List, Optional, Annotated

from fastapi import APIRouter, status, Depends, Query, Path, HTTPException
from sqlalchemy.orm import Session
from fastapi_limiter.depends import RateLimiter

from src.database.db import get_db
from src.database.models import User
from src.schemas import ContactModel, ContactResponse
from src.services.auth import auth_service
from src.repository import contacts as repository_contacts

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get("/upcoming_birthdays", response_model=List[ContactResponse])
async def get_contacts_by_upcoming_birthdays(
    limit: int = Query(10, le=500),
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
):
    """
    The get_contacts_by_upcoming_birthdays function returns a list of contacts with upcoming birthdays.

    :param limit: int: Set the limit of contacts returned
    :param le: Limit the number of contacts that can be returned
    :param offset: int: Specify the number of records to skip
    :param db: Session: Get a database session
    :param current_user: User: Get the current user from the database
    :return: A list of contacts
    :doc-author: Trelent
    """
    contacts = await repository_contacts.get_upcoming_birthdays(
        limit, offset, current_user, db
    )
    return contacts


@router.get("/", response_model=List[ContactResponse])
async def get_contacts(
    first_name: Annotated[str | None, Query(min_length=3, max_length=50)] = None,
    last_name: Annotated[str | None, Query(min_length=3, max_length=50)] = None,
    email: Annotated[str | None, Query(min_length=3, max_length=50)] = None,
    limit: Optional[int] = Query(10, le=500),
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
):
    """
    The get_contacts function returns a list of contacts.

    :param first_name: Annotated[str | None: Validate the first_name parameter
    :param last_name: Annotated[str | None: Specify the type of data that is expected
    :param email: Annotated[str | None: Validate the email address
    :param limit: Optional[int]: Limit the number of contacts returned
    :param offset: int: Skip the first n records
    :param db: Session: Pass the database session to the function
    :param current_user: User: Get the current user
    :return: A list of all contacts
    :doc-author: Trelent
    """
    contacts = await repository_contacts.get_contacts(
        limit, offset, current_user, db, first_name, last_name, email
    )
    return contacts


@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(
    contact_id: int = Path(ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
):
    """
    The get_contact function is a GET request that returns the contact with the given ID.
    The function takes in an integer as a path parameter, and uses it to query for the contact.
    If no such contact exists, then an HTTP 404 error is returned.

    :param contact_id: int: Get the id of the contact to be deleted
    :param db: Session: Get a database session
    :param current_user: User: Get the current user from the database
    :return: A contact object
    :doc-author: Trelent
    """
    contact = await repository_contacts.get_contact_by_id(contact_id, current_user, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    return contact


# RateLimiter need Redis
# @router.post("/", response_model=ContactResponse, status_code=status.HTTP_201_CREATED,
#              description='No more than 1 requests per 10 second', dependencies=[Depends(RateLimiter(times=1, seconds=10))])


@router.post("/", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(
    body: ContactModel,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
):
    """
    The create_contact function creates a new contact in the database.

    :param body: ContactModel: Pass the data from the request body to the function
    :param db: Session: Get the database session
    :param current_user: User: Get the user that is currently logged in
    :return: A contact model object
    :doc-author: Trelent
    """
    contact = await repository_contacts.create(body, current_user, db)
    return contact


@router.put("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    body: ContactModel,
    contact_id: int = Path(ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
):
    """
    The update_contact function updates a contact in the database.
        The function takes an id, body and db as parameters.
        It returns a ContactModel object.

    :param body: ContactModel: Pass the contact model
    :param contact_id: int: Specify the id of the contact to be deleted
    :param db: Session: Pass the database session to the repository
    :param current_user: User: Get the user who is logged in
    :return: A contact model
    :doc-author: Trelent
    """
    contact = await repository_contacts.update(contact_id, body, current_user, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    return contact


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_contact(
    contact_id: int = Path(ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
):
    """
    The remove_contact function removes a contact from the database.

    :param contact_id: int: Specify the path parameter in the url
    :param db: Session: Pass the database session to the function
    :param current_user: User: Get the user that is currently logged in
    :return: A contact object
    :doc-author: Trelent
    """
    contact = await repository_contacts.remove(contact_id, current_user, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    return contact
