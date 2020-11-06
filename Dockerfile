FROM python:3.6
ENV SEIR_HOME=/covid-seir/

RUN apt-get update
ARG REQUIREMENTS=requirements.txt
COPY $REQUIREMENTS /$REQUIREMENTS
RUN pip install -r /$REQUIREMENTS
ENV PYTHONPATH=$PYTHONPATH:$SEIR_HOME/src

# copy data
COPY data/ $SEIR_HOME/data

# source and tests
COPY pytest.ini $SEIR_HOME/pytest.ini

# DEV: tests/data accounts for almost entire MB footprint of tests/
# copy this first
COPY tests/data $SEIR_HOME/tests/data

# lightweight source
COPY src $SEIR_HOME/src
COPY tests/*.py $SEIR_HOME/tests/

WORKDIR $SEIR_HOME
