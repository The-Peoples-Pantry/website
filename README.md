# The People's Pantry Website

<p style="text-align:center">
  <a href="https://www.thepeoplespantryto.com">
    <img src="https://www.thepeoplespantryto.com/static/logo-black.png" width="20%">
  </a>
</p>

This repo hosts the code that runs thepeoplespantryto.com

The People's Pantry is a grassroots volunteer initiative dedicated to safely providing and delivering cooked meals and grocery packages to folks who have been disproportionately affected by the COVID-19 pandemic.

This website is a small-ish Python/Django application that serves up a form for recipients to request groceries and home-cooked meals, for chefs and deliverers to signup for those requests, and we use the Django admin to allow volunteer organizers to manage it all.

## Technology

Our driving technology principles are:

1. Accessibility
1. Simplicity
1. Collaboration

This application is used by a wide variety of people and it must be designed to be [accessible](https://www.a11yproject.com/checklist/) to their needs.

We strive to strike a balance between new features and code simplicity in order to make this application easy for new volunteers to onboard to.

We have deliberately chosen a "boring" tech stack that will be easy to debug, easy to deploy, and easy to learn. We use Python & [Django][django] to serve pages, [Gunicorn][gunicorn] as the web server, [Heroku][heroku] as our hosting provider, and [Postgres][postgres] as our backing relational database. We have avoided adding Javascript frameworks or client-side functionality to reduce the complexity of the application and keep accessibility levels high.

One area in which we have traded off some complexity for convenience is the use of a [bootstrap theme called landkit][landkit]. Those of us involved in the project don't have a deep background in design and wanted something that worked well and looked good without having to build our own design system.

## Contributing

We welcome contributions to this project! See our [Contributing guide][/contributing.md] and our [list of open issues](https://github.com/The-Peoples-Pantry/website/issues)

[django]: https://www.djangoproject.com/
[gunicorn]: https://gunicorn.org/
[heroku]: https://www.heroku.com/
[postgres]: https://www.postgresql.org/
[landkit]: https://landkit.goodthemes.co/
