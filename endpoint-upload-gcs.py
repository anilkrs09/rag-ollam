import os
import logging
from flask import Blueprint, request, jsonify
from google.cloud import storage

upload_bp = Blueprint("upload", __name__)

def upload_to_gcs(project_name: str, bucket_name: str, filename: str):
    try:
        client = storage.Client(project=project_name)
        bucket = client.bucket(bucket_name)
        blob_name = os.path.basename(filename)  # upload only file name
        blob = bucket.blob(blob_name)

        blob.upload_from_filename(filename)

        logging.info(f"Uploaded {filename} to gs://{bucket_name}/{blob_name}")
        return f"gs://{bucket_name}/{blob_name}"
    except Exception as e:
        logging.error(f"Error uploading file {filename} -> {e}")
        raise

@upload_bp.route("/upload", methods=["POST"])
def upload_file():
    try:
        data = request.get_json(force=True)
        project_name = data.get("project_name")
        bucket_name = data.get("bucket_name")
        filename = data.get("filename")

        if not project_name or not bucket_name or not filename:
            return jsonify({"error": "project_name, bucket_name and filename required"}), 400

        if not os.path.exists(filename):
            return jsonify({"error": f"File not found: {filename}"}), 404

        gcs_path = upload_to_gcs(project_name, bucket_name, filename)
        return jsonify({"status": "success", "gcs_path": gcs_path}), 200

    except Exception as e:
        logging.error(f"Upload failed: {e}")
        return jsonify({"error": str(e)}), 500
