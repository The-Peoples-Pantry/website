FROM python:3.9
WORKDIR /code
COPY requirements.txt /code/
RUN pip install -r requirements.txt
COPY . /code/
ENV DEBUG=True
RUN python website/manage.py collectstatic
RUN python website/manage.py migrate
ENV PORT=8000
EXPOSE ${PORT}
CMD ["sh", "-c", "python website/manage.py runserver 0.0.0.0:${PORT}"]
