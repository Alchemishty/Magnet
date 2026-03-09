"""Sanity check — verifies the test framework runs correctly."""


class TestSanity:
    def test_addition(self):
        # Arrange
        a, b = 1, 1

        # Act
        result = a + b

        # Assert
        assert result == 2

    def test_app_importable(self):
        # Act
        from app.main import app

        # Assert
        assert app.title == "Magnet API"
