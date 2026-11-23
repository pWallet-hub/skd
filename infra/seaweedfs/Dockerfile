# SeaweedFS with its S3 identities generated from environment variables at start-up,
# so credentials live in the deployment environment (not in git) and no bind mount is needed.
FROM chrislusf/seaweedfs:4.53
RUN mkdir -p /etc/seaweedfs
COPY generate-s3-config.sh /usr/local/bin/generate-s3-config.sh
RUN chmod +x /usr/local/bin/generate-s3-config.sh
ENTRYPOINT ["/usr/local/bin/generate-s3-config.sh"]
CMD ["server", "-dir=/data", "-ip.bind=0.0.0.0", "-master.volumeSizeLimitMB=1024", "-volume.max=0", "-s3", "-s3.port=8333", "-s3.config=/etc/seaweedfs/s3.json"]
