"""One error envelope for every API response:

    {"error": {"code": "...", "message": "...", "fields": {"field": ["msg"]}}}
"""
import logging

from django.http import Http404

from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler

log = logging.getLogger(__name__)


class BusinessError(Exception):
    """A rule of the bank was violated (as opposed to malformed input)."""

    def __init__(self, code: str, message: str, status_code: int = status.HTTP_422_UNPROCESSABLE_ENTITY, fields=None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.fields = fields or {}


def _envelope(code, message, fields=None):
    return {"error": {"code": code, "message": message, "fields": fields or {}}}


def _flatten(detail):
    if isinstance(detail, dict):
        return {k: _flatten(v) for k, v in detail.items()}
    if isinstance(detail, list):
        return [str(d) if not isinstance(d, (dict, list)) else _flatten(d) for d in detail]
    return [str(detail)]


def api_exception_handler(exc, context):
    if isinstance(exc, BusinessError):
        return Response(_envelope(exc.code, exc.message, exc.fields), status=exc.status_code)

    response = exception_handler(exc, context)
    if response is None:
        log.exception("Unhandled error", exc_info=exc)
        return Response(
            _envelope("server_error", "Something went wrong on our side. Please try again."),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    if isinstance(exc, ValidationError):
        fields = _flatten(exc.detail)
        if isinstance(fields, list):
            fields = {"non_field_errors": fields}
        if "non_field_errors" in fields:
            fields["_form"] = fields.pop("non_field_errors")
        response.data = _envelope("validation_error", "Please correct the highlighted fields.", fields)
    else:
        if isinstance(exc, Http404):
            code, message = "not_found", "We could not find what you were looking for."
        else:
            code = getattr(exc, "default_code", "error")
            message = str(getattr(exc, "detail", "Request failed."))
        response.data = _envelope(code, message)
    return response
