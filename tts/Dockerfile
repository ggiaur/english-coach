# Local text to speech (Piper, open source, CPU only). Serves POST /synthesize on port 5000.
FROM python:3.12-slim

RUN pip install --no-cache-dir "piper-tts[http]==1.8.0"

ARG VOICE=en_US-lessac-medium
ENV VOICE=${VOICE}
WORKDIR /voices
# The voice file is downloaded once while the image is built (needs internet at build time).
RUN python3 -m piper.download_voices ${VOICE}

EXPOSE 5000
CMD ["sh", "-c", "python3 -m piper.http_server -m ${VOICE} --data-dir /voices --host 0.0.0.0 --port 5000"]
