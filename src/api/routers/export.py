import os
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, status
from fastapi.responses import FileResponse
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_session
from services.export import ExportService

router = APIRouter(prefix="/export", tags=["Export"])


@router.post(
    "/generate",
    summary="Generate Data Export",
    description="Generate a tar.gz archive containing all documents in CSV, JSON, and raw HTML formats",
    status_code=status.HTTP_202_ACCEPTED,
)
async def generate_export(
    session: AsyncSession = Depends(get_session),
):
    """Generate and return a data export archive synchronously."""
    try:
        export_service = ExportService(session)
        archive_path = await export_service.export_all()

        return {
            "status": "completed",
            "archive_path": archive_path,
            "filename": os.path.basename(archive_path),
            "download_url": f"/api/v1/export/download/{os.path.basename(archive_path)}"
        }
    except Exception as e:
        logger.error(f"Export generation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export generation failed: {str(e)}"
        )


@router.post(
    "/generate-background",
    summary="Generate Data Export (Background)",
    description="Start generating a data export archive in the background",
    status_code=status.HTTP_202_ACCEPTED,
)
async def generate_export_background(
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
):
    """Start export generation in the background."""

    async def run_export():
        try:
            export_service = ExportService(session)
            archive_path = await export_service.export_all()
            logger.info(f"Background export completed: {archive_path}")
        except Exception as e:
            logger.error(f"Background export failed: {str(e)}")

    background_tasks.add_task(run_export)

    return {
        "status": "started",
        "message": "Export generation started in background. Check /api/v1/export/list for available exports."
    }


@router.get(
    "/download/{filename}",
    summary="Download Export Archive",
    description="Download a previously generated export archive",
    response_class=FileResponse,
)
async def download_export(filename: str):
    """Download an export archive."""
    export_dir = "exports"
    file_path = os.path.join(export_dir, filename)

    # Validate filename to prevent directory traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename"
        )

    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export file not found"
        )

    # Verify it's a tar.gz file
    if not filename.endswith(".tar.gz"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type"
        )

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/gzip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


@router.get(
    "/list",
    summary="List Available Exports",
    description="List all available export archives with metadata",
)
async def list_exports():
    """List available export archives."""
    export_dir = "exports"

    if not os.path.exists(export_dir):
        return {"exports": [], "total": 0}

    exports = []
    for filename in os.listdir(export_dir):
        if filename.endswith(".tar.gz"):
            file_path = os.path.join(export_dir, filename)
            try:
                size_bytes = os.path.getsize(file_path)
                size_mb = size_bytes / (1024 * 1024)
                modified_time = os.path.getmtime(file_path)

                exports.append({
                    "filename": filename,
                    "size_bytes": size_bytes,
                    "size_mb": round(size_mb, 2),
                    "modified_timestamp": modified_time,
                    "download_url": f"/api/v1/export/download/{filename}"
                })
            except Exception as e:
                logger.warning(f"Error reading file {filename}: {str(e)}")
                continue

    # Sort by modified time (newest first)
    exports.sort(key=lambda x: x["modified_timestamp"], reverse=True)

    return {
        "exports": exports,
        "total": len(exports)
    }


@router.delete(
    "/delete/{filename}",
    summary="Delete Export Archive",
    description="Delete a specific export archive",
)
async def delete_export(filename: str):
    """Delete an export archive."""
    export_dir = "exports"
    file_path = os.path.join(export_dir, filename)

    # Validate filename to prevent directory traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename"
        )

    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export file not found"
        )

    # Verify it's a tar.gz file
    if not filename.endswith(".tar.gz"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type"
        )

    try:
        os.remove(file_path)
        logger.info(f"Deleted export archive: {filename}")
        return {
            "status": "success",
            "message": f"Export archive '{filename}' deleted successfully"
        }
    except Exception as e:
        logger.error(f"Failed to delete export archive {filename}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete export archive: {str(e)}"
        )


@router.delete(
    "/cleanup",
    summary="Cleanup Old Exports",
    description="Delete export archives older than specified days",
)
async def cleanup_old_exports(
    days: int = 7,
):
    """Delete export archives older than specified number of days."""
    import time

    if days < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Days must be at least 1"
        )

    export_dir = "exports"

    if not os.path.exists(export_dir):
        return {
            "status": "success",
            "deleted": 0,
            "message": "No export directory found"
        }

    current_time = time.time()
    cutoff_time = current_time - (days * 24 * 60 * 60)

    deleted_files = []
    failed_files = []

    for filename in os.listdir(export_dir):
        if filename.endswith(".tar.gz"):
            file_path = os.path.join(export_dir, filename)
            try:
                modified_time = os.path.getmtime(file_path)
                if modified_time < cutoff_time:
                    os.remove(file_path)
                    deleted_files.append(filename)
                    logger.info(f"Deleted old export: {filename}")
            except Exception as e:
                logger.error(f"Failed to delete {filename}: {str(e)}")
                failed_files.append({"filename": filename, "error": str(e)})

    return {
        "status": "success",
        "deleted": len(deleted_files),
        "failed": len(failed_files),
        "deleted_files": deleted_files,
        "failed_files": failed_files if failed_files else None,
        "message": f"Deleted {len(deleted_files)} export(s) older than {days} days"
    }