FROM python:3.5

RUN apt-get update


ENV APP /app

RUN mkdir $APP
WORKDIR $APP

EXPOSE 5000

COPY ./app/requirements.txt .

RUN pip3 install -r requirements.txt

COPY ./app .

ENTRYPOINT ["python"]
CMD ["run.py"]

