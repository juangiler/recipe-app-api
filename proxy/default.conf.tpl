# 1. Define the upstream group for load balancing and reliability
upstream recipe_app {
    # This matches the service name in your docker-compose.yml
    server ${APP_HOST}:${APP_PORT};
}

server {
    listen ${LISTEN_PORT};

    # Serve static files directly
    location /static {
        alias /vol/static;
    }

    location /media {
        alias /vol/media;
    }

    # Proxy all traffic to the Django/Gunicorn app
    location / {
        proxy_pass http://recipe_app;

        # Standard headers to pass client information
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Required for WebSocket/ASGI support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Set max upload size
        client_max_body_size 10M;
    }
}