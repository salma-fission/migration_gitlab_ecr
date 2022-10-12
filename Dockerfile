FROM python:3.9

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /code

COPY requirements.txt .

RUN pip install -r requirements.txt

RUN apt-get update && apt-get -qq -y install \
  apt-transport-https \
  curl \
  unzip zip

RUN curl -fsSL https://get.docker.com -o get-docker.sh
RUN sh get-docker.sh

RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
RUN unzip awscliv2.zip
RUN ./aws/install
RUN aws --version

COPY src/ .

CMD [ "python", "." ]
