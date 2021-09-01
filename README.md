# The People's Pantry Website

Code repo that is running [thepeoplespantryto.com](https://www.thepeoplespantryto.com/)

## Technoologies Used

- Django

- Heroku

## Getting Started
0. Clone the project locally

    `git clone git@github.com:The-Peoples-Pantry/website.git` 

or if using https rather than ssh keys

    `git clone https://github.com/The-Peoples-Pantry/website.git`

### Using Docker

1. Build the image:

    `docker build -t tpp:latest .`

2. Run it:

    `docker run -dp 8000:8000 tpp:latest`

### Not a fan of Docker

1. Make sure you have the correct version of pythong installed

    `python --version` > 3

2. Install the project dependencies

    `pip install -r requirements.txt`

3. Collect the static files from all your django applications into one location
    
    `python website/manage.py collectstatic`

4. Run the DB migrations

    `python website/manage.py migrate`

5. Run the dev server (by default listens on port 8000)
    
    `python website/manage.py runserver`
