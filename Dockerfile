FROM python:3.9
WORKDIR /code
COPY requirements.txt /code/
RUN pip install -r requirements.txt
COPY . /code/
ENV DEBUG=True
ENV PORT=8000
EXPOSE ${PORT}
RUN python website/manage.py migrate
ENTRYPOINT ["python", "website/manage.py", "runserver", "0.0.0.0:8000"]
