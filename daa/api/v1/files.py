"""文件 API — 上传、预览、删除。"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File as FastAPIFile
from sqlalchemy.ext.asyncio import AsyncSession

from daa.db.session import get_db
from daa.middleware.auth import get_current_user
from daa.models.user import User
from daa.schemas.common import DeletedResponse
from daa.schemas.file import FileOut, FilePreviewOut, FileUploadResponse
from daa.services.file_service import (
    delete_file,
    get_file,
    preview_file,
    save_uploaded_file,
)
from daa.settings import get_settings

router = APIRouter(prefix="/files")


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = FastAPIFile(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """上传数据文件（CSV / Excel / JSON / Parquet）。"""
    settings = get_settings()

    # 检查扩展名
    ext = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in (file.filename or "") else ""
    allowed = settings.ALLOWED_UPLOAD_EXTENSIONS.split(",")
    if ext and ext not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {ext}，允许的类型: {allowed}",
        )

    # 检查大小
    content = await file.read()
    max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"文件大小超过限制 ({settings.MAX_UPLOAD_SIZE_MB}MB)",
        )

    # 保存
    analysis_file = await save_uploaded_file(
        db, user.id, file.filename or "unknown", content
    )
    await db.commit()

    return FileUploadResponse(
        file=FileOut.model_validate(analysis_file),
    )


@router.get("/{file_id}/preview", response_model=FilePreviewOut)
async def preview_uploaded_file(
    file_id: str,
    rows: int = 10,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """预览上传文件的前 N 行。"""
    result = await preview_file(db, file_id, user.id, rows=rows)
    if result is None:
        raise HTTPException(status_code=404, detail="文件不存在")
    return FilePreviewOut(**result)


@router.delete("/{file_id}", response_model=DeletedResponse)
async def remove_file(
    file_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除上传的文件。"""
    deleted = await delete_file(db, file_id, user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="文件不存在")
    await db.commit()
    return DeletedResponse(id=file_id)
