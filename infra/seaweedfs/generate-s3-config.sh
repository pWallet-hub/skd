#!/bin/sh
# Writes /etc/seaweedfs/s3.json from env vars, then starts SeaweedFS via the image's entrypoint.
set -e

: "${S3_ACCESS_KEY:?S3_ACCESS_KEY is required}"
: "${S3_SECRET_KEY:?S3_SECRET_KEY is required}"
: "${S3_BUCKET_PUBLIC:=smartkids-public}"

cat > /etc/seaweedfs/s3.json <<JSON
{
  "identities": [
    {
      "name": "smartkids-backend",
      "credentials": [{ "accessKey": "${S3_ACCESS_KEY}", "secretKey": "${S3_SECRET_KEY}" }],
      "actions": ["Admin", "Read", "List", "Tagging", "Write"]
    },
    {
      "name": "anonymous",
      "actions": ["Read:${S3_BUCKET_PUBLIC}"]
    }
  ]
}
JSON
chmod 644 /etc/seaweedfs/s3.json
echo "SeaweedFS S3 identities written (public bucket: ${S3_BUCKET_PUBLIC})"

exec /entrypoint.sh "$@"
