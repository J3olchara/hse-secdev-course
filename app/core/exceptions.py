class ApiError(Exception):
    def __init__(self, code: str, message: str, status: int = 400):
        self.code = code
        self.message = message
        self.status = status
        super().__init__(self.message)

    def __str__(self):
        return self.message


class ValidationError(ApiError):
    def __init__(self, message: str = "Validation error"):
        super().__init__("validation_error", message, 422)


class NotFoundError(ApiError):
    def __init__(self, message: str = "Resource not found"):
        super().__init__("not_found", message, 404)


class UnauthorizedError(ApiError):
    def __init__(self, message: str = "Unauthorized"):
        super().__init__("unauthorized", message, 401)


class ForbiddenError(ApiError):
    def __init__(self, message: str = "Forbidden"):
        super().__init__("forbidden", message, 403)


class ConflictError(ApiError):
    def __init__(self, message: str = "Conflict"):
        super().__init__("conflict", message, 409)


class DatabaseError(ApiError):
    def __init__(self, message: str = "Database error"):
        super().__init__("database_error", message, 500)


class BusinessLogicError(ApiError):
    def __init__(self, message: str = "Business logic error"):
        super().__init__("business_error", message, 400)
