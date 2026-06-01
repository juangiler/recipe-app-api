# Recipe App API

A Django-based Recipe API project using Docker for development.

## Getting Started

### Prerequisites
- Docker
- Docker Compose

### Building the Application

To build the Docker images, run:

```bash
docker compose build
```

### Running the Application

To start the application and database:

```bash
docker compose up
```

The API will be available at `http://localhost:8000`.

### Running Specific Commands

You can run Django management commands or other tools inside the Docker container using `docker compose run`.

#### Running Tests

To run the Django test suite:

```bash
docker compose run --rm app sh -c "python manage.py test"
```

#### Running Flake8 (Code Linting)

To check code style with Flake8:

```bash
docker compose run --rm app sh -c "flake8"
```

#### Other Django Commands

For example, to create a superuser:

```bash
docker compose run --rm app sh -c "python manage.py createsuperuser"
```

Or to run migrations:

```bash
docker compose run --rm app sh -c "python manage.py migrate"
```

### Development Workflow

1. Make changes to your code in the `app/` directory.
2. Build and run: `docker compose up --build`
3. Run tests: `docker compose run --rm app sh -c "python manage.py test"`
4. Check code style: `docker compose run --rm app sh -c "flake8"`

### Stopping the Application

To stop the running containers:

```bash
docker compose down
```

To also remove volumes (including database data) and reset the database state:

```bash
docker compose down -v
```

To start the containers again in detached mode (running in the background):

```bash
docker compose up -d
```

- `docker compose down` stops and removes containers, networks, and default volumes.
- `docker compose down -v` also removes named volumes, which resets database data and other persisted storage.
- `docker compose up -d` starts the services in the background so the terminal is free to use for other commands.
