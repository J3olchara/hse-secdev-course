"""
Unit тесты для валидации входных данных (ADR-004)
"""

import pytest
from pydantic import ValidationError

from app.schemas.user import UserBase, UserLogin, UserUpdate
from app.schemas.wish import WishCreate, WishUpdate


class TestWishValidation:
    """Тесты валидации Wish schemas"""

    def test_valid_wish_creation(self):
        """Валидный wish должен пройти валидацию"""
        wish = WishCreate(title="My wish", description="This is a valid wish")
        assert wish.title == "My wish"
        assert wish.description == "This is a valid wish"

    def test_wish_title_too_short(self):
        """Title не может быть пустым (ADR-004)"""
        with pytest.raises(ValidationError) as exc:
            WishCreate(title="", description="test")

        errors = exc.value.errors()
        assert any(e["loc"][0] == "title" for e in errors)

    def test_wish_title_too_long(self):
        """Title не может быть длиннее 200 символов (ADR-004)"""
        with pytest.raises(ValidationError) as exc:
            WishCreate(title="A" * 201, description="test")

        errors = exc.value.errors()
        assert any(e["loc"][0] == "title" for e in errors)

    def test_wish_description_too_long(self):
        """Description не может быть длиннее 5000 символов (ADR-004)"""
        with pytest.raises(ValidationError) as exc:
            WishCreate(title="Test", description="B" * 5001)

        errors = exc.value.errors()
        assert any(e["loc"][0] == "description" for e in errors)

    def test_wish_blocks_xss_in_title(self):
        """Блокировка XSS в title (ADR-004, R7)"""
        with pytest.raises(ValidationError) as exc:
            WishCreate(title="<script>alert(1)</script>", description="test")

        errors = exc.value.errors()
        assert any("HTML/JS" in str(e["msg"]) for e in errors)

    def test_wish_blocks_xss_in_description(self):
        """Блокировка XSS в description (ADR-004, R7)"""
        with pytest.raises(ValidationError) as exc:
            WishCreate(
                title="Test", description="<script>alert('xss')</script>"
            )

        errors = exc.value.errors()
        assert any("HTML/JS" in str(e["msg"]) for e in errors)

    def test_wish_blocks_javascript_protocol(self):
        """Блокировка javascript: protocol (ADR-004)"""
        with pytest.raises(ValidationError) as exc:
            WishCreate(title="javascript:alert(1)", description="test")

        errors = exc.value.errors()
        assert any("HTML/JS" in str(e["msg"]) for e in errors)

    def test_wish_blocks_event_handlers(self):
        """Блокировка HTML event handlers (ADR-004)"""
        dangerous_inputs = [
            "Test onerror=alert(1)",
            "Test onclick=malicious()",
        ]

        for inp in dangerous_inputs:
            with pytest.raises(ValidationError):
                WishCreate(title=inp, description="test")

    def test_wish_update_validation(self):
        """WishUpdate должен иметь такую же валидацию"""
        # Валидный update
        update = WishUpdate(title="Updated title")
        assert update.title == "Updated title"

        # Невалидный - XSS
        with pytest.raises(ValidationError):
            WishUpdate(description="<script>bad()</script>")

    def test_wish_strips_whitespace(self):
        """Whitespace должен быть удален (ADR-004)"""
        wish = WishCreate(title="  My wish  ", description="  Some text  ")
        assert wish.title == "My wish"
        assert wish.description == "Some text"


class TestUserValidation:
    """Тесты валидации User schemas"""

    def test_valid_user(self):
        """Валидный user должен пройти валидацию"""
        user = UserBase(username="john_doe", email="john@example.com")
        assert user.username == "john_doe"
        assert user.email == "john@example.com"

    def test_username_too_short(self):
        """Username меньше 3 символов отклоняется (ADR-004)"""
        with pytest.raises(ValidationError) as exc:
            UserBase(username="ab", email="test@example.com")

        errors = exc.value.errors()
        assert any(e["loc"][0] == "username" for e in errors)

    def test_username_too_long(self):
        """Username длиннее 50 символов отклоняется (ADR-004)"""
        with pytest.raises(ValidationError) as exc:
            UserBase(username="a" * 51, email="test@example.com")

        errors = exc.value.errors()
        assert any(e["loc"][0] == "username" for e in errors)

    def test_username_invalid_characters(self):
        """Username должен содержать только буквы, цифры, - и _ (ADR-004)"""
        invalid_usernames = [
            "user@name",
            "user name",
            "user.name",
            "user<script>",
            "user!name",
        ]

        for username in invalid_usernames:
            with pytest.raises(ValidationError) as exc:
                UserBase(username=username, email="test@example.com")

            errors = exc.value.errors()
            assert any(
                "letters, numbers, dashes" in str(e["msg"]) for e in errors
            ), f"Username {username} должен быть отклонен"

    def test_username_valid_characters(self):
        """Валидные символы в username (ADR-004)"""
        valid_usernames = [
            "john_doe",
            "user123",
            "test-user",
            "User_123-test",
        ]

        for username in valid_usernames:
            user = UserBase(username=username, email="test@example.com")
            assert user.username == username

    def test_email_validation(self):
        """Email должен быть валидным (ADR-004)"""
        # Валидный email
        user = UserBase(username="test", email="valid@example.com")
        assert user.email == "valid@example.com"

        # Невалидные emails
        invalid_emails = [
            "notanemail",
            "@example.com",
            "user@",
            "user @example.com",
        ]

        for email in invalid_emails:
            with pytest.raises(ValidationError):
                UserBase(username="test", email=email)

    def test_password_minimum_length(self):
        """Пароль должен быть минимум 8 символов (ADR-004, NFR-01)"""
        with pytest.raises(ValidationError) as exc:
            UserLogin(username="test", password="short")

        errors = exc.value.errors()
        assert any(e["loc"][0] == "password" for e in errors)

    def test_password_maximum_length(self):
        """Пароль не может быть длиннее 128 символов (ADR-004)"""
        with pytest.raises(ValidationError) as exc:
            UserLogin(username="test", password="A" * 129)

        errors = exc.value.errors()
        assert any(e["loc"][0] == "password" for e in errors)

    def test_password_requires_letter_and_digit(self):
        """Пароль должен содержать букву и цифру (ADR-004, NFR-01)"""
        # Только цифры
        with pytest.raises(ValidationError) as exc:
            UserUpdate(password="12345678")

        errors = exc.value.errors()
        assert any("letter" in str(e["msg"]).lower() for e in errors)

        # Только буквы
        with pytest.raises(ValidationError) as exc:
            UserUpdate(password="password")

        errors = exc.value.errors()
        assert any("digit" in str(e["msg"]).lower() for e in errors)

    def test_password_valid_combination(self):
        """Валидный пароль с буквами и цифрами (ADR-004)"""
        valid_passwords = [
            "Password1",
            "Test1234",
            "abc123xyz",
            "MyP@ssw0rd",
        ]

        for password in valid_passwords:
            user = UserUpdate(password=password)
            assert user.password == password


class TestEdgeCases:
    """Тесты граничных случаев"""

    def test_wish_exactly_200_chars(self):
        """Title ровно 200 символов должен быть принят"""
        title = "A" * 200
        wish = WishCreate(title=title, description="test")
        assert len(wish.title) == 200

    def test_wish_exactly_5000_chars_description(self):
        """Description ровно 5000 символов должен быть принят"""
        desc = "B" * 5000
        wish = WishCreate(title="Test", description=desc)
        assert len(wish.description) == 5000

    def test_username_exactly_3_chars(self):
        """Username ровно 3 символа должен быть принят"""
        user = UserBase(username="abc", email="test@example.com")
        assert len(user.username) == 3

    def test_username_exactly_50_chars(self):
        """Username ровно 50 символов должен быть принят"""
        username = "a" * 50
        user = UserBase(username=username, email="test@example.com")
        assert len(user.username) == 50

    def test_password_exactly_8_chars(self):
        """Пароль ровно 8 символов с буквой и цифрой должен быть принят"""
        user = UserUpdate(password="Pass1234")
        assert len(user.password) == 8

    def test_none_description_allowed(self):
        """Description может быть None (опциональное поле)"""
        wish = WishCreate(title="Test", description=None)
        assert wish.description is None

        # Или вообще не указано
        wish2 = WishCreate(title="Test")
        assert wish2.description is None
