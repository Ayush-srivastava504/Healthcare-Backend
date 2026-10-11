# One error shape for the whole API:
# {"status_code": 400, "message": "...", "errors": {...} or null}
from django.db import IntegrityError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


def api_exception_handler(exc, context):
    if isinstance(exc, IntegrityError):
        return Response(
            {
                "status_code": status.HTTP_409_CONFLICT,
                "message": "The request conflicts with existing data.",
                "errors": None,
            },
            status=status.HTTP_409_CONFLICT,
        )

    response = exception_handler(exc, context)
    if response is None:
        return None

    if response.status_code == status.HTTP_400_BAD_REQUEST:
        message, errors = "Validation failed.", response.data
    else:
        detail = response.data.get("detail") if isinstance(response.data, dict) else None
        message, errors = str(detail or "Request failed."), None

    response.data = {
        "status_code": response.status_code,
        "message": message,
        "errors": errors,
    }
    return response
