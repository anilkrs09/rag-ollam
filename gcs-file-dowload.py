Python scipt to download
import json
import time
from concurrent.futures import TimeoutError
from google.cloud import pubsub_v1, storage

# CONFIG
PROJECT_ID = "your-project-id"
SUBSCRIPTION_ID = "your-subscription-id"  # The one connected to your GCS notifications
DOWNLOAD_DIR = "./downloads"  # Where to save files

# Init clients
subscriber = pubsub_v1.SubscriberClient()
storage_client = storage.Client()

subscription_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_ID)

def download_file(bucket_name, file_name):
    """Download a file from GCS to local directory."""
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)
    local_path = f"{DOWNLOAD_DIR}/{file_name.split('/')[-1]}"
    blob.download_to_filename(local_path)
    print(f"✅ Downloaded {file_name} from {bucket_name} to {local_path}")

def callback(message):
    """Process incoming Pub/Sub messages."""
    try:
        # Pub/Sub message data from GCS is in JSON format
        data = json.loads(message.data.decode("utf-8"))

        bucket_name = data["bucket"]
        file_name = data["name"]

        print(f"📦 New file detected: {file_name} in bucket {bucket_name}")
        download_file(bucket_name, file_name)

        message.ack()

    except Exception as e:
        print(f"❌ Error processing message: {e}")
        message.nack()

def main():
    print("🚀 Listening for new GCS file events...")
    streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)

    try:
        streaming_pull_future.result()  # Keeps the service alive
    except KeyboardInterrupt:
        streaming_pull_future.cancel()

if __name__ == "__main__":
    main()

=======Docker=====
FROM python:3.11-slim

# Install dependencies
RUN pip install --no-cache-dir google-cloud-pubsub google-cloud-storage

# Copy code
WORKDIR /app
COPY main.py .

# Set env vars (override in Helm)
ENV PROJECT_ID=""
ENV SUBSCRIPTION_ID=""
ENV DOWNLOAD_DIR="/downloads"

# Create download dir
RUN mkdir -p /downloads

CMD ["python", "main.py"]

======= Chart.yaml
apiVersion: v2
name: gcs-listener
description: GCS Pub/Sub file downloader
type: application
version: 0.1.0
appVersion: "1.0"

=== Values.yaml

replicaCount: 1

image:
  repository: your-dockerhub-user/gcs-listener
  tag: latest
  pullPolicy: IfNotPresent

serviceAccount:
  create: true
  name: ""

googleProjectId: "your-gcp-project-id"
subscriptionId: "your-subscription-id"
downloadDir: "/downloads"

# GCP Service Account JSON key (base64 encoded)
gcpCredentials: ""

resources: {}

========Deployment======
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "gcs-listener.fullname" . }}
  labels:
    {{- include "gcs-listener.labels" . | nindent 4 }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      app: {{ include "gcs-listener.name" . }}
  template:
    metadata:
      labels:
        app: {{ include "gcs-listener.name" . }}
    spec:
      serviceAccountName: {{ include "gcs-listener.fullname" . }}
      containers:
        - name: gcs-listener
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          env:
            - name: PROJECT_ID
              value: "{{ .Values.googleProjectId }}"
            - name: SUBSCRIPTION_ID
              value: "{{ .Values.subscriptionId }}"
            - name: DOWNLOAD_DIR
              value: "{{ .Values.downloadDir }}"
            - name: GOOGLE_APPLICATION_CREDENTIALS
              value: "/var/secrets/google/credentials.json"
          volumeMounts:
            - name: gcp-creds
              mountPath: /var/secrets/google
              readOnly: true
            - name: download-dir
              mountPath: {{ .Values.downloadDir }}
      volumes:
        - name: gcp-creds
          secret:
            secretName: gcs-credentials
        - name: download-dir
          emptyDir: {}


