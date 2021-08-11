# -*- coding: utf-8 -*-
from pprint import pformat
from operator import itemgetter
import html
from functools import wraps


class VariableDoesNotExist(Exception):

    def __init__(self, msg, params=()):
        self.msg = msg
        self.params = params

    def __str__(self):
        return self.msg % self.params


def pprint(value):
    """A wrapper around pprint.pprint -- for debugging, really."""
    try:
        return pformat(value)
    except Exception as e:
        return "Error in formatting: %s: %s" % (e.__class__.__name__, e)


def add(value, arg):
    """Add the arg to the value."""
    try:
        return int(value) + int(arg)
    except (ValueError, TypeError):
        try:
            return value + arg
        except Exception: # noqa
            return ''


def dictsort(value, arg):
    """
    Given a list of dicts, return that list sorted by the property given in
    the argument.
    """
    try:
        return sorted(value, key=itemgetter(arg))
    except (TypeError, VariableDoesNotExist):
        return ''


def _safety_decorator(safety_marker, func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        return safety_marker(func(*args, **kwargs))

    return wrapped


class SafeData:
    def __html__(self):
        """
        Return the html representation of a string for interoperability.
        This allows other template engines to understand Django's SafeData.
        """
        return self


class SafeString(str, SafeData):
    """
    A str subclass that has been specifically marked as "safe" for HTML output
    purposes.
    """

    def __add__(self, rhs):
        """
        Concatenating a safe string with another safe bytestring or
        safe string is safe. Otherwise, the result is no longer safe.
        """
        t = super().__add__(rhs)
        if isinstance(rhs, SafeData):
            return SafeString(t)
        return t

    def __str__(self):
        return self


def mark_safe(s):
    """
    Explicitly mark a string as safe for (HTML) output purposes. The returned
    object can be used everywhere a string is appropriate.
    If used on a method as a decorator, mark the returned data as safe.
    Can be called multiple times on a single string.
    """
    if hasattr(s, '__html__'):
        return s
    if callable(s):
        return _safety_decorator(mark_safe, s)
    return SafeString(s)


def escape(text):
    """
    Return the given text with ampersands, quotes and angle brackets encoded
    for use in HTML.
    Always escape input, even if it's already escaped and marked as such.
    This may result in double-escaping. If this is a concern, use
    conditional_escape() instead.
    """
    return mark_safe(html.escape(str(text)))


def force_escape(value):
    """
    Escape a string's HTML. Return a new string containing the escaped
    characters (as opposed to "escape", which marks the content for later
    possible escaping).
    """
    return escape(value)
