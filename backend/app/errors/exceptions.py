from typing import Optional, Union

from fastapi import HTTPException


class ErrorCodeException(HTTPException):
    def __init__(
        self,
        status_code: int,
        error_code: Union[str, object],
        detail: Optional[str] = None,
    ):
        code = error_code.value if hasattr(error_code, "value") else str(error_code)
        self.error_code = code
        self.message_detail = detail
        super().__init__(status_code=status_code, detail=detail or code)
