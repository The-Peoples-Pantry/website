# Contributing

## Getting started

1. First, clone this project

```sh
# With SSH
git clone git@github.com:The-Peoples-Pantry/website.git

# or with HTTPS
git clone https://github.com/The-Peoples-Pantry/website.git
```

## Running the application

This application can be run within a [Docker][docker] container, or with Python on your host machine. You might prefer the Docker approach if you're not used to running Python applications locally. You might prefer the Python approach if you're comfortable with Python applications and configuring virtual environments and `pip` requirements.

### With Docker

1. Build and run the Docker image

```sh
docker build -t tpp:latest . && docker run -dp 8000:8000 tpp:latest
```

2. Access the server at http://0.0.0.0:8000

If you need to run any other commands using the application (such as test commands, migrations, etc) you can execute them within the running Docker container using [`docker exec`](https://docs.docker.com/engine/reference/commandline/exec/)

### With Python

1. Make sure you have the correct version of Python installed

```sh
python --version
# Should report version 3
```

2. (Optionally) If you don't have the correct version of Python installed, install it using [pyenv][pyenv]

3. Create a virtual environment to store your dependencies, then activate that virtual environment

```sh
python -m venv venv
source venv/bin/activate
```

4. Install the Python dependencies

```sh
pip install -r requirements.txt
```

5. Apply the database migrations to setup your database

```sh
python website/manage.py migrate
```

5. Run the dev server (by default it listens on port 8000)

```sh
DEBUG=1 python website/manage.py runserver
```

6. Access the server at http://0.0.0.0:8000

### Writing & Running Tests

The full test suite can be run with:

```sh
python website/manage.py test website
```

Django has [extensive documentation][django-testing] on testing practices, and we ask that contributors add tests with their functionality.

In addition to functional tests, we also test our style using the [flake8][flake8] linting tool. It can be run with:

```sh
flake8 website
```

If any style violations are detected, they'll be printed to the console.

### Pull requests

Contributors can suggest changes through GitHub Pull Requests (PRs), we use GitHub actions to automatically run our test suite against each PR to ensure that the change does not break anything.

When a PR is merged, it will be automatically deployed to Heroku and you can expect it to be live on the website within 5 minutes.

[flake8]: https://flake8.pycqa.org/en/latest/
[django-testing]: https://docs.djangoproject.com/en/stable/topics/testing/
[docker]: https://www.docker.com/
[pyenv]: https://github.com/pyenv/pyenv
