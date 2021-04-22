FROM python:3.8-alpine
RUN apk update && apk add --virtual build-dependencies build-base gcc zlib-dev jpeg-dev
RUN apk add --update --no-cache ffmpeg
WORKDIR /app
COPY . /app
RUN pip install -r requirements.txt
CMD python main.py /app/config/config.json
