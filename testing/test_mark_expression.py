from typing import Callable

import pytest
from _pytest.mark.expression import Expression
from _pytest.mark.expression import ParseError


def evaluate(input: str, matcher: Callable[[str], bool]) -> bool:
    return Expression.compile(input).evaluate(matcher)


def test_empty_is_false() -> None:
    assert not evaluate("", lambda ident: False)
    assert not evaluate("", lambda ident: True)
    assert not evaluate("   ", lambda ident: False)
    assert not evaluate("\t", lambda ident: False)


@pytest.mark.parametrize(
    ("expr", "expected"),
    (
        ("true", True),
        ("true", True),
        ("false", False),
        ("not true", False),
        ("not false", True),
        ("not not true", True),
        ("not not false", False),
        ("true and true", True),
        ("true and false", False),
        ("false and true", False),
        ("true and true and true", True),
        ("true and true and false", False),
        ("true and true and not true", False),
        ("false or false", False),
        ("false or true", True),
        ("true or true", True),
        ("true or true or false", True),
        ("true and true or false", True),
        ("not true or true", True),
        ("(not true) or true", True),
        ("not (true or true)", False),
        ("true and true or false and false", True),
        ("true and (true or false) and false", False),
        ("true and (true or (not (not false))) and false", False),
    ),
)
def test_basic(expr: str, expected: bool) -> None:
    matcher = {"true": True, "false": False}.__getitem__
    assert evaluate(expr, matcher) is expected


@pytest.mark.parametrize(
    ("expr", "expected"),
    (
        ("               true           ", True),
        ("               ((((((true))))))           ", True),
        ("     (         ((\t  (((true)))))  \t   \t)", True),
        ("(     true     and   (((false))))", False),
        ("not not not not true", True),
        ("not not not not not true", False),
    ),
)
def test_syntax_oddeties(expr: str, expected: bool) -> None:
    matcher = {"true": True, "false": False}.__getitem__
    assert evaluate(expr, matcher) is expected


@pytest.mark.parametrize(
    ("expr", "column", "message"),
    (
        ("(", 2, "expected not OR left parenthesis OR identifier; got end of input"),
        (" (", 3, "expected not OR left parenthesis OR identifier; got end of input",),
        (
            ")",
            1,
            "expected not OR left parenthesis OR identifier; got right parenthesis",
        ),
        (
            ") ",
            1,
            "expected not OR left parenthesis OR identifier; got right parenthesis",
        ),
        ("not", 4, "expected not OR left parenthesis OR identifier; got end of input",),
        (
            "not not",
            8,
            "expected not OR left parenthesis OR identifier; got end of input",
        ),
        (
            "(not)",
            5,
            "expected not OR left parenthesis OR identifier; got right parenthesis",
        ),
        ("and", 1, "expected not OR left parenthesis OR identifier; got and"),
        (
            "ident and",
            10,
            "expected not OR left parenthesis OR identifier; got end of input",
        ),
        ("ident and or", 11, "expected not OR left parenthesis OR identifier; got or",),
        ("ident ident", 7, "expected end of input; got identifier"),
    ),
)
def test_syntax_errors(expr: str, column: int, message: str) -> None:
    with pytest.raises(ParseError) as excinfo:
        evaluate(expr, lambda ident: True)
    assert excinfo.value.column == column
    assert excinfo.value.message == message


@pytest.mark.parametrize(
    "ident",
    (
        ".",
        "...",
        ":::",
        "a:::c",
        "a+-b",
        "אבגד",
        "aaאבגדcc",
        "a[bcd]",
        "1234",
        "1234abcd",
        "1234and",
        "notandor",
        "not_and_or",
        "not[and]or",
        "1234+5678",
        "123.232",
        "if",
        "else",
        "while",
    ),
)
def test_valid_idents(ident: str) -> None:
    assert evaluate(ident, {ident: True}.__getitem__)


@pytest.mark.parametrize(
    ("constant", "expected"),
    (
        ("True", True),
        ("False", False),
        ("None", None),
    ),
)
def test_constants(constant: str, expected: bool) -> None:
    """Test that True/False/None are treated as Python constants, not identifiers."""
    # The matcher function should not be called for these constants
    result = evaluate(constant, lambda ident: not expected)
    assert result is expected


def test_constants_in_expressions() -> None:
    """Test that constants work correctly in complex expressions."""
    # Test boolean operations with constants
    assert evaluate("True and False", lambda x: True) is False
    assert evaluate("True or False", lambda x: False) is True
    assert evaluate("not True", lambda x: True) is False
    assert evaluate("not False", lambda x: False) is True
    
    # Test constants mixed with identifiers
    matcher = {"test": True, "other": False}.__getitem__
    assert evaluate("True and test", matcher) is True
    assert evaluate("False or test", matcher) is True
    assert evaluate("True and other", matcher) is False
    assert evaluate("False or other", matcher) is False
    
    # Test None behavior
    assert evaluate("None or True", lambda x: False) is True
    assert evaluate("True and None", lambda x: False) is None


@pytest.mark.parametrize(
    "ident",
    (
        "/",
        "\\",
        "^",
        "*",
        "=",
        "&",
        "%",
        "$",
        "#",
        "@",
        "!",
        "~",
        "{",
        "}",
        '"',
        "'",
        "|",
        ";",
        "←",
    ),
)
def test_invalid_idents(ident: str) -> None:
    with pytest.raises(ParseError):
        evaluate(ident, lambda ident: True)
