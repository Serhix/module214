import datetime
import unittest
from unittest.mock import MagicMock

from libgravatar import Gravatar
from sqlalchemy import and_
from sqlalchemy.orm import Session

from src.database.models import User
from src.schemas import UserModel

from src.repository.users import (
    get_user_by_email,
    create_user,
    update_token,
    update_avatar,
    confirmed_email,
    update_password,
)


class TestContacts(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.session = MagicMock(spec=Session)

    async def test_ger_user_by_email(self):
        email = 'test@gmail.com'
        user = User(email=email)
        self.session.query().filter().first.return_value = user
        result = await get_user_by_email(email, db=self.session)
        self.assertEqual(result, user)

    async def test_greate_user(self):

        body = UserModel(
            username='Testuser',
            email='test@gmail.com',
            password="testpass1234",
        )
        result = await create_user(body=body, db=self.session)
        self.assertEqual(result.username, body.username)
        self.assertEqual(result.email, body.email)
        self.assertEqual(result.password, body.password)

    async def test_update_token(self):
        user = User()
        refresh_token = "asdasdasdasdasdasdasd.rtertertertert.erttyrtyrtyrtyrt"
        await update_token(user, refresh_token, self.session)
        self.assertEqual(user.refresh_token, refresh_token)

    async def test_update_avatar(self):
        email = 'test@gmail.com'
        url = 'test.image.com'
        user = User(email=email)
        result = await update_avatar(email, url, self.session)
        self.assertEqual(result.avatar, url)

    async def test_confirmed_email(self):
        email = 'test@gmail.com'
        user = User(email=email, confirmed=False)
        self.session.query().filter().first.return_value = user
        await confirmed_email(email, self.session)
        self.assertEqual(user.confirmed, True)

    async def test_update_password(self):
        user = User()
        test_hash_pass = 'sdkjlfsdlkfjnsdlkjfnsdlkfsdlkfjsdfsdf234234nb23'
        self.session.query().filter().first.return_value = user
        result = await update_password(user, test_hash_pass, self.session)
        self.assertEqual(user.password, test_hash_pass)


if __name__ == '__main__':
    unittest.main()