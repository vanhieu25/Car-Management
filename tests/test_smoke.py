"""Smoke test to verify test infrastructure works."""

import pytest


def test_true_is_true():
    """Smoke test - assert True passes."""
    assert True


def test_false_is_not_true():
    """Smoke test - assert False is not True."""
    assert not False


def test_basic_math():
    """Smoke test - basic math operations."""
    assert 1 + 1 == 2
    assert 10 - 5 == 5
    assert 3 * 3 == 9


def test_string_operations():
    """Smoke test - string operations."""
    assert "car" + "management" == "carmanagement"
    assert "hello".upper() == "HELLO"


def test_list_operations():
    """Smoke test - list operations."""
    lst = [1, 2, 3]
    assert len(lst) == 3
    assert sum(lst) == 6
    assert max(lst) == 3
    assert min(lst) == 1