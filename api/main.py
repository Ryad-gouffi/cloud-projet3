from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
from minio import Minio
from minio.error import S3Error
import psycopg2
from datetime import datetime
import hashlib
import io
import time

app = FastAPI(title="MinIO File API")

# -------------------- MinIO CONFIG --------------------
MINIO_CLIENT = Minio(
    "minio:9000",
    access_key="admin",
    secret_key="password123",
    secure=False
)

BUCKET_NAME = "uploads"

# Create bucket if not exists
if not MINIO_CLIENT.bucket_exists(BUCKET_NAME):
    MINIO_CLIENT.make_bucket(BUCKET_NAME)

# -------------------- DATABASE CONFIG --------------------
def get_db_connection():
    while True:
        try:
            conn = psycopg2.connect(
                host="db",
                database="filesdb",
                user="user",
                password="password"
            )
            return conn
        except:
            print("Database not ready, waiting...")
            time.sleep(2)

conn = get_db_connection()
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS files (
    id SERIAL PRIMARY KEY,
    filename TEXT UNIQUE,
    size_bytes BIGINT,
    content_type TEXT,
    sha256 TEXT,
    upload_date TIMESTAMP
)
""")
conn.commit()

# -------------------- UPLOAD FILE --------------------
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    data = await file.read()

    # Upload to MinIO
    MINIO_CLIENT.put_object(
        bucket_name=BUCKET_NAME,
        object_name=file.filename,
        data=io.BytesIO(data),
        length=len(data),
        content_type=file.content_type
    )

    # Compute SHA-256
    sha256 = hashlib.sha256(data).hexdigest()

    # Store metadata in DB
    cursor.execute(
        """
        INSERT INTO files (filename, size_bytes, content_type, sha256, upload_date)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (filename) DO NOTHING
        """,
        (file.filename, len(data), file.content_type, sha256, datetime.utcnow())
    )
    conn.commit()

    return {
        "message": "File uploaded successfully",
        "filename": file.filename
    }

# -------------------- DOWNLOAD FILE --------------------
@app.get("/download/{filename}")
def download_file(filename: str):
    try:
        obj = MINIO_CLIENT.get_object(BUCKET_NAME, filename)
        return StreamingResponse(
            obj,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except S3Error:
        return {"error": "File not found"}

# -------------------- DELETE FILE --------------------
@app.delete("/delete/{filename}")
def delete_file(filename: str):
    try:
        MINIO_CLIENT.remove_object(BUCKET_NAME, filename)
        cursor.execute("DELETE FROM files WHERE filename = %s", (filename,))
        conn.commit()
        return {"message": "File deleted", "filename": filename}
    except S3Error:
        return {"error": "File not found"}

# -------------------- METADATA --------------------
@app.get("/metadata/{filename}")
def get_metadata(filename: str):
    cursor.execute(
        "SELECT filename, size_bytes, content_type, sha256, upload_date FROM files WHERE filename = %s",
        (filename,)
    )
    row = cursor.fetchone()

    if not row:
        return {"error": "Metadata not found"}

    return {
        "filename": row[0],
        "size_bytes": row[1],
        "content_type": row[2],
        "sha256": row[3],
        "upload_date": row[4]
    }