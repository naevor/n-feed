import contextvars
import logging
import uuid

_request_id = contextvars.ContextVar("request_id", default="-")


def clean_request_id(value):
    value = (value or "").strip()
    if not value or len(value) > 100 or "\r" in value or "\n" in value:
        return uuid.uuid4().hex
    return value


def get_request_id():
    return _request_id.get()


def set_request_id(value):
    return _request_id.set(value)


def reset_request_id(token):
    _request_id.reset(token)


class RequestIDFilter(logging.Filter):
    def filter(self, record):
        record.request_id = get_request_id()
        return True
