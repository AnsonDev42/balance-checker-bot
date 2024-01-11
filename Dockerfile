FROM python:3.12.1-slim

LABEL authors="AnsonDev42"
WORKDIR /src/app
RUN apt-get -y update; apt-get -y install curl
RUN apt-get install -y --no-install-recommends python3-dev libpq-dev gcc
COPY requirements.txt requirements.txt
RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
RUN python get-pip.py
RUN pip install -r requirements.txt
RUN pip install supervisor
COPY docker/supervisord.conf /etc/
# Make port 8000 available to the world outside this container
EXPOSE 8000

# Run supervisord
ENV PATH="/root/.local/bin:$PATH"
COPY balance_checker /src/app/balance_checker
WORKDIR /src/app/balance_checker
CMD ["supervisord", "-c", "/etc/supervisord.conf"]
EXPOSE 8000
