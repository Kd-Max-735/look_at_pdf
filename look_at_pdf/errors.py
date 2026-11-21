"""Shared error codes for the converter and MCP wrapper."""

SUCCESS = 0
ERR_FILE_NOT_FOUND = 1001
ERR_UNSUPPORTED_FILE = 1002
ERR_ENCRYPTED_PDF = 1003
ERR_DAMAGED_FILE = 1004
ERR_BLANK_DOCUMENT = 1005
ERR_OCR_UNAVAILABLE = 1006
ERR_PORT_OCCUPIED = 1007
ERR_UNKNOWN = 1999

ERROR_MESSAGES = {
    SUCCESS: "success",
    ERR_FILE_NOT_FOUND: "file_path does not exist",
    ERR_UNSUPPORTED_FILE: "unsupported file type; use PDF/PNG/JPG/JPEG/TIFF/BMP",
    ERR_ENCRYPTED_PDF: "encrypted PDF is not supported",
    ERR_DAMAGED_FILE: "file is damaged or unreadable",
    ERR_BLANK_DOCUMENT: "no recognizable content found",
    ERR_OCR_UNAVAILABLE: "OCR backend is unavailable",
    ERR_PORT_OCCUPIED: "MCP server port is occupied",
    ERR_UNKNOWN: "unknown error",
}


class ConvertError(Exception):
    """Expected conversion error with a stable return code."""

    def __init__(self, code: int, detail: str | None = None) -> None:
        self.code = code
        self.detail = detail
        msg = ERROR_MESSAGES.get(code, ERROR_MESSAGES[ERR_UNKNOWN])
        if detail:
            msg = f"{msg}: {detail}"
        super().__init__(msg)
