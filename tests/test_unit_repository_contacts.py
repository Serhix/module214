import datetime
import unittest
from unittest.mock import MagicMock

from sqlalchemy import and_
from sqlalchemy.orm import Session

from src.database.models import Contact, User
from src.schemas import ContactModel, ContactResponse
from src.repository.contacts import (
    get_contacts,
    get_contact_by_id,
    create,
    update,
    remove,
    get_upcoming_birthdays,
)


class TestContacts(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.session = MagicMock(spec=Session)
        self.user = User(id=1)

    async def test_ger_contacts(self):
        contacts = [Contact(), Contact(), Contact()]
        self.session.query().filter_by().limit().offset().all.return_value = contacts
        result = await get_contacts(
            limit=10,
            offset=0,
            user=self.user,
            db=self.session,
            first_name=None,
            last_name=None,
            email=None,
        )
        self.assertEqual(result, contacts)

    async def test_ger_contacts_with_filter(self):
        first_name = "first_test_name"
        last_name = "last_test_name"
        test_email = "test_email@gmail.com"
        contact_1 = Contact(first_name=first_name)
        contact_2 = Contact(last_name=last_name)
        contact_3 = Contact(email=test_email)
        contacts = [contact_1, contact_2, contact_3]
        self.session.query().filter().limit().offset().all.return_value = contacts
        result = await get_contacts(
            10, 0, self.user, self.session, first_name, last_name, test_email
        )
        self.assertEqual(len(result), 3)

    async def test_ger_contacts_by_id(self):
        contact = Contact()
        self.session.query().filter().first.return_value = contact
        result = await get_contact_by_id(contact_id=1, user=self.user, db=self.session)
        self.assertEqual(result, contact)

    async def test_ger_contacts_by_id_not_found(self):
        self.session.query().filter().first.return_value = None
        result = await get_contact_by_id(contact_id=1, user=self.user, db=self.session)
        self.assertIsNone(result)

    async def test_create_contact(self):
        body = ContactModel(
            first_name="test",
            last_name="test",
            email="test@gmail.com",
            phone="0980000000",
            birthday=datetime.datetime.now(),
            description="test",
            favorites=False,
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
        )
        result = await create(body=body, user=self.user, db=self.session)
        self.assertEqual(result.first_name, body.first_name)
        self.assertEqual(result.last_name, body.last_name)
        self.assertEqual(result.email, body.email)
        self.assertEqual(result.birthday, body.birthday)
        self.assertTrue(hasattr(result, "id"))

    async def test_remove_contact_found(self):
        contact = Contact()
        self.session.query().filter().first.return_value = contact
        result = await remove(contact_id=1, user=self.user, db=self.session)
        self.assertEqual(result, contact)

    async def test_remove_contact_found_not_found(self):
        self.session.query().filter().first.return_value = None
        result = await remove(contact_id=1, user=self.user, db=self.session)
        self.assertIsNone(result)

    async def test_update_contact(self):
        body = ContactModel(
            first_name="test",
            last_name="test",
            email="test@gmail.com",
            phone="0980000000",
            birthday=datetime.datetime.now(),
            description="test",
            favorites=False,
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
        )
        contact = Contact()
        self.session.query().filter().first.return_value = contact
        self.session.commit.return_value = None
        result = await update(contact_id=1, body=body, user=self.user, db=self.session)
        self.assertEqual(result, contact)

        body = ContactModel(
            first_name="test",
            last_name="test",
            email="test@gmail.com",
            phone="0980000000",
            birthday=datetime.datetime.now(),
            description="test",
            favorites=False,
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
        )
        self.session.query().filter().first.return_value = None
        self.session.commit.return_value = None
        result = await update(contact_id=1, body=body, user=self.user, db=self.session)
        self.assertIsNone(result)

    async def test_get_upcoming_birthdays_2(self):
        contact_1 = Contact(
            id=1,
            user_id=1,
            first_name="John Doe",
            birthday=datetime.datetime.now().date() + datetime.timedelta(days=2),
        )
        contact_2 = Contact(
            id=2,
            user_id=1,
            first_name="Jane Doe",
            birthday=datetime.datetime.now().date() + datetime.timedelta(days=3),
        )
        contacts = [contact_1, contact_2]
        self.session.query().filter().limit().offset().all.return_value = contacts
        upcoming_birthdays = await get_upcoming_birthdays(
            limit=10, offset=0, user=self.user, db=self.session
        )

        self.assertEqual(len(upcoming_birthdays), 2)
        self.assertEqual(upcoming_birthdays[0].id, 1)
        self.assertEqual(upcoming_birthdays[0].first_name, "John Doe")
        self.assertEqual(upcoming_birthdays[1].id, 2)
        self.assertEqual(upcoming_birthdays[1].first_name, "Jane Doe")


if __name__ == "__main__":
    unittest.main()
