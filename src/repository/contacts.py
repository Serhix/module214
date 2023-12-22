from datetime import datetime, timedelta

from sqlalchemy import and_
from sqlalchemy.orm import Session

from src.database.models import Contact, User
from src.schemas import ContactModel


async def get_contacts(
    limit: int, offset: int, user: User, db: Session, first_name, last_name, email
):
    """
    The get_contacts function returns a list of contacts for the user.
        The function takes in three parameters: limit, offset, and user.
        Limit is an integer that specifies how many contacts to return at once.
        Offset is an integer that specifies where to start returning contacts from (for pagination).
        User is a User object containing information about the current logged-in user.

    :param limit: int: Limit the number of contacts returned
    :param offset: int: Specify the number of records to skip before returning results
    :param user: User: Get the user_id of the logged-in user
    :param db: Session: Access the database
    :param first_name: Filter the contacts by first name
    :param last_name: Filter the contacts by last name
    :param email: Filter the contacts by email
    :return: A list of contacts that match the search criteria
    :doc-author: Trelent
    """
    contacts_by_first_name = []
    contacts_by_last_name = []
    contacts_by_email = []
    if first_name is not None:
        contacts_by_first_name = (
            db.query(Contact)
            .filter(
                and_(
                    Contact.user_id == user.id, Contact.first_name.contains(first_name)
                )
            )
            .limit(limit)
            .offset(offset)
            .all()
        )
    if last_name is not None:
        contacts_by_last_name = (
            db.query(Contact)
            .filter(
                and_(Contact.user_id == user.id, Contact.last_name.contains(last_name))
            )
            .limit(limit)
            .offset(offset)
            .all()
        )
    if email is not None:
        contacts_by_email = (
            db.query(Contact)
            .filter(and_(Contact.user_id == user.id, Contact.email.contains(email)))
            .limit(limit)
            .offset(offset)
            .all()
        )
    contacts = set(contacts_by_first_name + contacts_by_last_name + contacts_by_email)
    if contacts:
        return contacts
    else:
        contacts = (
            db.query(Contact)
            .filter_by(user_id=user.id)
            .limit(limit)
            .offset(offset)
            .all()
        )
    return contacts


async def get_contact_by_id(contact_id: int, user: User, db: Session):
    """
    The get_contact_by_id function returns a contact object from the database based on the user's id and the contact's id.
    The function takes in three parameters:
        -contact_id: an integer representing the unique identifier of a specific contact.
        -user: an object representing a user that is logged into our application. This parameter is used to ensure that only
        contacts belonging to this particular user are returned by this function.
        -db: an SQLAlchemy Session instance, which represents our connection to the database.

    :param contact_id: int: Specify the id of the contact that we want to retrieve
    :param user: User: Get the user's id
    :param db: Session: Pass in the database session
    :return: A contact object
    :doc-author: Trelent"""
    contact = (
        db.query(Contact)
        .filter(and_(Contact.user_id == user.id, Contact.id == contact_id))
        .first()
    )
    return contact


async def create(body: ContactModel, user: User, db: Session):
    """
    The create function creates a new contact in the database.
        Args:
            body (ContactModel): The contact to create.
            user (User): The current user, used for authorization purposes.

    :param body: ContactModel: Get the data from the request body
    :param user: User: Get the user id from the token
    :param db: Session: Access the database
    :return: The contact object
    :doc-author: Trelent
    """
    contact = Contact(user_id=user.id, **body.model_dump())
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


async def update(contact_id: int, body: ContactModel, user: User, db: Session):
    """
    The update function updates a contact in the database.
        Args:
            contact_id (int): The id of the contact to update.
            body (ContactModel): The updated information for the specified contact.

    :param contact_id: int: Identify the contact we want to update
    :param body: ContactModel: Pass the data from the request body into this function
    :param user: User: Check if the user is logged-in
    :param db: Session: Access the database
    :return: The contact object
    :doc-author: Trelent
    """
    contact = await get_contact_by_id(contact_id, user, db)
    if contact:
        contact.first_name = body.first_name
        contact.last_name = body.last_name
        contact.email = body.email
        contact.phone = body.phone
        contact.birthday = body.birthday
        contact.description = body.description
        contact.favorites = body.favorites
        db.commit()
    return contact


async def remove(contact_id: int, user: User, db: Session):
    """
    The remove function removes a contact from the database.
        Args:
            contact_id (int): The id of the contact to be removed.
            user (User): The user who is removing the contact.
            db (Session): A connection to our database, used for querying and updating data.

    :param contact_id: int: Specify the contact to be deleted
    :param user: User: Get the user id of the current logged-in user
    :param db: Session: Pass the database session to the function
    :return: The contact that was deleted
    :doc-author: Trelent
    """
    contact = await get_contact_by_id(contact_id, user, db)
    if contact:
        db.delete(contact)
        db.commit()
    return contact


async def get_upcoming_birthdays(limit: int, offset: int, user: User, db: Session):
    """
    The get_upcoming_birthdays function returns a list of contacts whose birthdays are within the next week.
        Args:
            limit (int): The maximum number of items to return.
            offset (int): The number of items to skip before returning results.
            user (User): A User object representing the current user making this request. This is used for authorization purposes, as only contacts belonging to this user will be returned in the response body.

    :param limit: int: Limit the number of results returned by the query
    :param offset: int: Determine how many contacts to skip before returning the results
    :param user: User: Get the user id of the current user
    :param db: Session: Pass the database session to the function
    :return: A list of contacts that have birthdays in the next week
    :doc-author: Trelent
    """

    next_week = datetime.now().date() + timedelta(weeks=1)
    # print(next_week)
    contacts = (
        db.query(Contact)
        .filter(
            and_(
                Contact.user_id == user.id,
                Contact.birthday >= datetime.now().date(),
                Contact.birthday <= next_week,
            )
        )
        .limit(limit)
        .offset(offset)
        .all()
    )
    # print(contacts[0].birthday)
    # print(contacts[1].birthday)
    # print('len: ', len(contacts), 'user: ', user.id)
    return contacts
