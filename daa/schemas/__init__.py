"""Pydantic 请求/响应模型。"""

from daa.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserOut,
)
from daa.schemas.common import (
    DeletedResponse,
    ErrorResponse,
    PaginatedResponse,
    PaginationParams,
    StatusResponse,
)
from daa.schemas.session import (
    SessionCreate,
    SessionDetailOut,
    SessionListOut,
    SessionOut,
)
from daa.schemas.analysis import (
    AnalysisCreateResponse,
    AnalysisStepOut,
    FigureOut,
    ReportOut,
    StreamProgressEvent,
)
from daa.schemas.file import FileOut, FilePreviewOut, FileUploadResponse
from daa.schemas.config import UserConfigOut, UserConfigUpdate
from daa.schemas.rag import RagSearchResponse, RagSearchResult

__all__ = [
    # Auth
    "RegisterRequest",
    "LoginRequest",
    "TokenResponse",
    "UserOut",
    # Common
    "PaginationParams",
    "PaginatedResponse",
    "ErrorResponse",
    "StatusResponse",
    "DeletedResponse",
    # Session
    "SessionCreate",
    "SessionOut",
    "SessionDetailOut",
    "SessionListOut",
    # Analysis
    "AnalysisCreateResponse",
    "AnalysisStepOut",
    "FigureOut",
    "ReportOut",
    "StreamProgressEvent",
    # File
    "FileOut",
    "FilePreviewOut",
    "FileUploadResponse",
    # Config
    "UserConfigOut",
    "UserConfigUpdate",
    # RAG
    "RagSearchResponse",
    "RagSearchResult",
]
