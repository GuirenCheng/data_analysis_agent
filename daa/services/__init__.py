"""业务逻辑服务层。"""

from daa.services.auth_service import (
    authenticate_user,
    create_access_token,
    decode_access_token,
    hash_password,
    register_user,
    verify_password,
)
from daa.services.session_service import (
    create_session,
    delete_session,
    get_session,
    list_sessions,
    update_session_status,
)
from daa.services.analysis_service import (
    cancel_analysis,
    persist_step,
    run_analysis,
)
from daa.services.file_service import (
    delete_file,
    get_file,
    preview_file,
    save_uploaded_file,
)
from daa.services.config_service import get_user_config, update_user_config
from daa.services.rag_service import index_session, search_similar
from daa.services.report_service import get_report

__all__ = [
    # Auth
    "hash_password",
    "verify_password",
    "create_access_token",
    "decode_access_token",
    "register_user",
    "authenticate_user",
    # Session
    "create_session",
    "get_session",
    "list_sessions",
    "update_session_status",
    "delete_session",
    # Analysis
    "run_analysis",
    "persist_step",
    "cancel_analysis",
    # File
    "save_uploaded_file",
    "get_file",
    "delete_file",
    "preview_file",
    # Config
    "get_user_config",
    "update_user_config",
    # RAG
    "search_similar",
    "index_session",
    # Report
    "get_report",
]
