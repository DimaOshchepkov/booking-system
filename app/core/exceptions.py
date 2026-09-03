class BookingError(Exception):
    def __init__(self, message: str, field: str | None = None):
        self.message = message
        self.field = field
        super().__init__(message)



class SlotUnavailableError(BookingError):
    def __init__(self):
        super().__init__(
            message="Выбранное время уже забронировано",
            field="booking_time"
        )
        
class BookingNotFoundError(BookingError):
    def __init__(self, booking_id: int):
        super().__init__(
            message=f"Бронь с id={booking_id} не найдена",
            field="booking_id",
        )