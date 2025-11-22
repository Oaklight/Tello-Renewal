"""Tests for web element locators."""

import pytest
from selenium.webdriver.common.by import By

from src.tello_renewal.web.elements.locators import Locator, TelloLocators


class TestLocator:
    """Test Locator class."""

    def test_creation(self):
        """Test creating a locator."""
        locator = Locator(by=By.CSS_SELECTOR, value="#test", description="Test element")

        assert locator.by == By.CSS_SELECTOR
        assert locator.value == "#test"
        assert locator.description == "Test element"
        assert locator.fallbacks == []

    def test_creation_with_fallbacks(self):
        """Test creating a locator with fallbacks."""
        fallback = Locator(By.ID, "test", "Fallback")
        locator = Locator(
            by=By.CSS_SELECTOR,
            value="#test",
            description="Test element",
            fallbacks=[fallback],
        )

        assert len(locator.fallbacks) == 1
        assert locator.fallbacks[0] == fallback

    def test_by_value_tuple(self):
        """Test by_value_tuple method."""
        locator = Locator(by=By.CSS_SELECTOR, value="#test", description="Test element")

        result = locator.by_value_tuple()
        assert result == (By.CSS_SELECTOR, "#test")

    def test_invalid_by_type_raises_error(self):
        """Test that invalid by type raises error."""
        with pytest.raises(ValueError, match="Invalid locator type"):
            Locator(by="invalid_type", value="#test", description="Test element")


class TestTelloLocators:
    """Test TelloLocators class."""

    def test_login_locators(self):
        """Test login page locators."""
        assert TelloLocators.LOGIN_EMAIL.by == By.CSS_SELECTOR
        assert TelloLocators.LOGIN_EMAIL.value == "input#i_username"
        assert "email" in TelloLocators.LOGIN_EMAIL.description.lower()

        assert TelloLocators.LOGIN_PASSWORD.by == By.CSS_SELECTOR
        assert TelloLocators.LOGIN_PASSWORD.value == "input#i_current_password"
        assert "password" in TelloLocators.LOGIN_PASSWORD.description.lower()

    def test_dashboard_locators(self):
        """Test dashboard page locators."""
        assert TelloLocators.RENEWAL_DATE.by == By.CSS_SELECTOR
        assert TelloLocators.RENEWAL_DATE.value == "span.card_text > span"

        assert TelloLocators.RENEW_BUTTON.by == By.CSS_SELECTOR
        assert TelloLocators.RENEW_BUTTON.value == "button#renew_plan"

    def test_balance_locators(self):
        """Test balance related locators."""
        assert TelloLocators.BALANCE_PACK_CARDS.by == By.CSS_SELECTOR
        assert TelloLocators.BALANCE_PACK_CARDS.value == ".pack_card"
        assert len(TelloLocators.BALANCE_PACK_CARDS.fallbacks) > 0

        assert TelloLocators.BALANCE_DETAILS.by == By.CSS_SELECTOR
        assert TelloLocators.BALANCE_DETAILS.value == ".balance-details"

    def test_plan_locators(self):
        """Test plan information locators."""
        assert TelloLocators.PLAN_DATA.by == By.CSS_SELECTOR
        assert TelloLocators.PLAN_DATA.value == "div.subtitle > div.subtitle_heading"

        assert TelloLocators.PLAN_MINUTES.by == By.CSS_SELECTOR
        assert TelloLocators.PLAN_MINUTES.value == "div.subtitle > div:nth-child(4)"

        assert TelloLocators.PLAN_TEXTS.by == By.CSS_SELECTOR
        assert TelloLocators.PLAN_TEXTS.value == "div.subtitle > div:nth-child(5)"

    def test_renewal_page_locators(self):
        """Test renewal page locators."""
        assert TelloLocators.CARD_EXPIRY_MONTH.by == By.CSS_SELECTOR
        assert TelloLocators.CARD_EXPIRY_MONTH.value == "select#cc_expiry_month"

        assert TelloLocators.CARD_EXPIRY_YEAR.by == By.CSS_SELECTOR
        assert TelloLocators.CARD_EXPIRY_YEAR.value == "select#cc_expiry_year"

        assert TelloLocators.NOTIFICATION_CHECKBOX.by == By.CSS_SELECTOR
        assert "checkbox" in TelloLocators.NOTIFICATION_CHECKBOX.value

        assert TelloLocators.FINALIZE_ORDER_BUTTON.by == By.CSS_SELECTOR
        assert (
            TelloLocators.FINALIZE_ORDER_BUTTON.value
            == "button#checkout_form_submit_holder"
        )

    def test_get_all_locators(self):
        """Test getting all locators."""
        locators = TelloLocators.get_all_locators()
        assert len(locators) > 0

        # Check that all returned items are Locator instances
        for locator in locators:
            assert isinstance(locator, Locator)
            assert locator.by is not None
            assert locator.value is not None
            assert locator.description is not None

    def test_validate_all_locators(self):
        """Test validating all locators."""
        # Should not raise any exception
        result = TelloLocators.validate_all_locators()
        assert result is True

    def test_locator_descriptions_are_meaningful(self):
        """Test that all locators have meaningful descriptions."""
        locators = TelloLocators.get_all_locators()

        for locator in locators:
            # Description should not be empty and should be descriptive
            assert len(locator.description) > 5
            assert locator.description != locator.value
            assert not locator.description.isspace()
