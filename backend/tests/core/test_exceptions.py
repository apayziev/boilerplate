from fastapi import status

from app.core.exceptions import (
    BadRequestException,
    DuplicateValueException,
    ForbiddenException,
    NotFoundException,
    RateLimitException,
    UnauthorizedException,
    UnprocessableEntityException,
)


def test_bad_request_exception():
    exc = BadRequestException()
    assert exc.status_code == status.HTTP_400_BAD_REQUEST
    assert exc.detail == "Noto'g'ri so'rov"


def test_not_found_exception():
    exc = NotFoundException()
    assert exc.status_code == status.HTTP_404_NOT_FOUND
    assert exc.detail == "Topilmadi"


def test_forbidden_exception():
    exc = ForbiddenException()
    assert exc.status_code == status.HTTP_403_FORBIDDEN
    assert exc.detail == "Ruxsat berilmagan"


def test_unauthorized_exception():
    exc = UnauthorizedException()
    assert exc.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc.detail == "Tizimga kirilmagan"
    assert exc.headers["WWW-Authenticate"] == "Bearer"


def test_unprocessable_entity_exception():
    exc = UnprocessableEntityException()
    assert exc.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert exc.detail == "Qayta ishlab bo'lmaydigan ma'lumot"


def test_duplicate_value_exception():
    exc = DuplicateValueException()
    assert exc.status_code == status.HTTP_409_CONFLICT
    assert exc.detail == "Takroriy qiymat"


def test_rate_limit_exception():
    exc = RateLimitException()
    assert exc.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    assert exc.detail == "So'rovlar chegarasidan oshib ketdi"


def test_custom_exception_messages():
    exc = BadRequestException(detail="Custom Error")
    assert exc.detail == "Custom Error"
