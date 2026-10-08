"""文件服务 — 文件上传、存储、预览。"""

import os
import uuid
from pathlib import Path
from typing import Optional

import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from daa.models.analysis_file import AnalysisFile
from daa.settings import get_settings


UPLOAD_DIR = Path("uploads")


async def save_uploaded_file(
    db: AsyncSession,
    user_id: str,
    filename: str,
    content: bytes,
    session_id: Optional[str] = None,
) -> AnalysisFile:
    """保存上传的文件到磁盘并创建数据库记录。"""
    settings = get_settings()

    # 确保上传目录存在
    upload_path = Path(settings.UPLOAD_DIR)
    upload_path.mkdir(parents=True, exist_ok=True)

    # 生成唯一文件名
    file_id = str(uuid.uuid4())
    ext = Path(filename).suffix
    stored_name = f"{file_id}{ext}"
    stored_path = upload_path / stored_name

    # 写入磁盘
    with open(stored_path, "wb") as f:
        f.write(content)

    # 检测列名和行数
    columns_detected = None
    row_count = None
    try:
        if ext.lower() in (".csv",):
            df = pd.read_csv(stored_path, nrows=0, encoding="utf-8")
            columns_detected = list(df.columns)
        elif ext.lower() in (".xlsx", ".xls"):
            df = pd.read_excel(stored_path, nrows=0)
            columns_detected = list(df.columns)
    except Exception:
        pass

    # 尝试获取行数
    try:
        if ext.lower() in (".csv",):
            df = pd.read_csv(stored_path)
            row_count = len(df)
    except Exception:
        pass

    # 创建数据库记录
    analysis_file = AnalysisFile(
        id=file_id,
        user_id=user_id,
        session_id=session_id,
        original_name=filename,
        stored_path=str(stored_path.resolve()),
        file_size=len(content),
        mime_type=_guess_mime_type(ext),
        columns_detected=columns_detected,
        row_count=row_count,
    )
    db.add(analysis_file)
    await db.flush()
    return analysis_file


async def get_file(
    db: AsyncSession, file_id: str, user_id: str
) -> Optional[AnalysisFile]:
    """获取文件记录。"""
    result = await db.execute(
        select(AnalysisFile).where(
            AnalysisFile.id == file_id,
            AnalysisFile.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def delete_file(db: AsyncSession, file_id: str, user_id: str) -> bool:
    """删除文件记录和磁盘文件。"""
    analysis_file = await get_file(db, file_id, user_id)
    if not analysis_file:
        return False

    # 删除磁盘文件
    try:
        os.remove(analysis_file.stored_path)
    except OSError:
        pass

    await db.delete(analysis_file)
    await db.flush()
    return True


async def preview_file(
    db: AsyncSession, file_id: str, user_id: str, rows: int = 10
) -> Optional[dict]:
    """预览文件内容（前 N 行）。"""
    analysis_file = await get_file(db, file_id, user_id)
    if not analysis_file:
        return None

    try:
        ext = Path(analysis_file.original_name).suffix.lower()
        if ext == ".csv":
            df = pd.read_csv(analysis_file.stored_path, nrows=rows)
        elif ext in (".xlsx", ".xls"):
            df = pd.read_excel(analysis_file.stored_path, nrows=rows)
        else:
            return {"columns": [], "rows": [], "total_rows": 0}

        return {
            "columns": list(df.columns),
            "rows": df.values.tolist(),
            "total_rows": analysis_file.row_count or 0,
        }
    except Exception:
        return {"columns": [], "rows": [], "total_rows": 0}


def _guess_mime_type(ext: str) -> str:
    """根据扩展名猜测 MIME 类型。"""
    mapping = {
        ".csv": "text/csv",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".xls": "application/vnd.ms-excel",
        ".json": "application/json",
        ".parquet": "application/octet-stream",
    }
    return mapping.get(ext.lower(), "application/octet-stream")
