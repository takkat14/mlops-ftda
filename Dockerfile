FROM python:3.9

RUN echo 'Launched build!'
WORKDIR /usr/src/web

RUN echo 'Copying project files'
ADD api /usr/src/web/api
ADD configs /usr/src/web/configs
COPY app.py configurator.py logger.py /usr/src/web/
COPY README.md /usr/src/web/
RUN chmod -R 777 /usr/src/web/

RUN echo 'Copying poetry files'
COPY poetry.lock pyproject.toml /usr/src/web/
RUN pip3 install poetry

RUN echo 'Installing dependencies'
RUN poetry install

# RUN echo 'Exposing ports'
# EXPOSE 5001 9090

RUN echo 'Adding run command'
ENV RUNTIME_DOCKER Yes
CMD poetry run python app.py