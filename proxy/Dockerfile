FROM nginxinc/nginx-unprivileged:1-alpine
LABEL maintainer="juangiler"


COPY ./default.conf.tpl /etc/nginx/default.conf.tpl
COPY ./run.sh /run.sh


ENV LISTEN_PORT=8000
ENV APP_HOST=app
ENV APP_PORT=9000

USER root

# Create the static and media directories
# We create them so the Nginx user has access
RUN mkdir -p /vol/static && \
    mkdir -p /vol/media && \
    chmod -R 755 /vol && \
    touch /etc/nginx/conf.d/default.conf && \
    chown nginx:nginx /etc/nginx/conf.d/default.conf && \
    chmod +x /run.sh



# Define volumes
VOLUME /vol

# Switch back to the non-privileged user for security
USER nginx

CMD [ "/run.sh" ]