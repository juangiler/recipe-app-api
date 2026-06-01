FROM python:3.9-slim
LABEL maintainer="juangiler"

ENV PYTHONUNBUFFERED=1


# copy requirements and install
COPY ./requirements.txt /tmp/requirements.txt
COPY ./requirements.dev.txt /tmp/requirements.dev.txt
# copy the app directory 
COPY ./app /app
# copy the script folder
COPY ./scripts /scripts


# set working directory
WORKDIR /app
# expose the port from the container to our host
EXPOSE 8000

ARG DEV=false

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
        postgresql-client \
        libjpeg-dev \
        build-essential \
        libpq-dev && \
    python -m venv /py && \
    /py/bin/pip install --upgrade pip && \
    /py/bin/pip install -r /tmp/requirements.txt && \
    apt-get remove -y build-essential libpq-dev && \
    rm -rf /var/lib/apt/lists/*


# Install dev requirements if DEV=true
RUN if [ "$DEV" = "true" ] ; then \
      /py/bin/pip install -r /tmp/requirements.dev.txt ; \
    fi

# Clean up temp files
RUN rm -rf /tmp/*

# Create django user with home directory (Debian syntax)
RUN mkdir -p /home/django-user/.vscode-server/bin && \
    adduser \
        --disabled-password \
        --gecos "" \
        --home /home/django-user \
        django-user && \
    chown -R django-user:django-user /home/django-user

RUN mkdir -p /vol/web/media && \
    mkdir -p /vol/web/static && \
    chown -R django-user:django-user /vol && \
    chmod -R 755 /vol && \
    chmod -R +x /scripts



ENV PATH="/scripts:/py/bin:$PATH"

USER django-user


CMD [ "run.sh" ]