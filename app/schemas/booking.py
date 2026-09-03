# app/schemas/booking.py
import re
from datetime import date, time, timedelta
from typing import Literal

from pydantic import BaseModel, Field, field_validator

ALLOWED_TIME_SLOTS = {time(hour=h) for h in range(12, 23)}


class BookingCreate(BaseModel):
    name: str = Field(max_length=100)
    phone: str
    booking_date: date
    booking_time: time
    guests: int = Field(ge=1, le=12)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Имя должно содержать минимум 2 символа")
        if not re.match(r"^[A-Za-zА-Яа-яЁё\s\-]+$", v):
            raise ValueError("Имя может содержать только буквы, пробелы и дефис")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        v = v.strip()
        if not re.match(r"^(\+7|8)\d{10}$", v):
            raise ValueError(
                "Телефон должен быть в формате +7XXXXXXXXXX или 8XXXXXXXXXX"
            )
        return v

    @field_validator("booking_date")
    @classmethod
    def validate_booking_date(cls, v: date) -> date:
        today = date.today()
        max_date = today + timedelta(days=90)
        if v < today:
            raise ValueError("Дата бронирования не может быть в прошлом")
        if v > max_date:
            raise ValueError("Дата бронирования не может быть позднее 90 дней")
        return v

    @field_validator("booking_time")
    @classmethod
    def validate_booking_time(cls, v: time) -> time:
        if v not in ALLOWED_TIME_SLOTS:
            slots_str = ", ".join(
                t.strftime("%H:%M") for t in sorted(ALLOWED_TIME_SLOTS)
            )
            raise ValueError(f"Допустимое время бронирования: {slots_str}")
        return v


class BookingOut(BookingCreate):
    id: int
    status: Literal["active", "cancelled"]
