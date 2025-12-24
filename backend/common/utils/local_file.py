import os
import uuid
import shutil
from fastapi import UploadFile

UPLOAD_DIR = "static/uploads"


class LocalFileUtils:
    @staticmethod
    def init_dir():
        if not os.path.exists(UPLOAD_DIR):
            os.makedirs(UPLOAD_DIR)

    @staticmethod
    async def upload(file: UploadFile) -> str:
        LocalFileUtils.init_dir()
        # 生成唯一文件名
        ext = os.path.splitext(file.filename)[1]
        new_name = f"{uuid.uuid4().hex}{ext}"
        file_path = os.path.join(UPLOAD_DIR, new_name)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return new_name

    @staticmethod
    def get_file_path(file_id: str) -> str:
        return os.path.join(UPLOAD_DIR, file_id)