# ML-OPS. The Good, the Bad and the Ugly
## What's going on?
Here you can find Flask-based web application for very dummy text classification models.

## Components:
* `app.py` -- main starter is here
* `api` -- contains both `src` and `endpoints.py`
* `src` -- data access objects, model trainers and so on. Internal logic implementation
* `endpoints.py` -- contains API documentaion and implementation. Swagger friendly :)
* `configs` -- yaml configs directory for fancy hydra-based configs.
* `configurator.py` -- global config is generated here
* `logger.py` -- it was a time, I would like to record logs, but, well... Global as configurator is.

## How to run on my local machine?
Prequisits: you need Docker :( because mongoDB and MinIO were pulled and run in the background
```
docker pull mongo
docker run --name mongodb -d -p 27017:27017 mongo
```
```
docker run \
    -p 9000:9000 \
    -p 9090:9090 \
    --name minio \
    -v /minio/data:/data \
    -e "MINIO_ROOT_USER=preffered_username_but_change_it_in_configs_firstly" \
    -e "MINIO_ROOT_PASSWORD=preffered_password_but_change_it_in_configs_firstly" \
    quay.io/minio/minio server /data --console-address ":9090"
```

Next, you need to install `poetry` and python requirements.
```
pip3 install poetry
poetry install
```
You are almost there, it's enough to run:
```
poetry run python app.py
```
Basically, Swagger should be opened at `127.0.0.1:5001`, welcome to play :)

You also may access to MinIO console, it's `127.0.0.1:9090`.

## How to run via docker?
```
docker pull mongo
docker run --name mongodb -d -p 27017:27017 mongo
```
```
docker run \
    -p 9000:9000 \
    -p 9090:9090 \
    --name minio \
    -v /minio/data:/data \
    -e "MINIO_ROOT_USER=preffered_username_but_change_it_in_configs_firstly" \
    -e "MINIO_ROOT_PASSWORD=preffered_password_but_change_it_in_configs_firstly" \
    quay.io/minio/minio server /data --console-address ":9090"
```
The image is pushed to DockerHub, therefore we can pull it. BE AWARE: I build the image on M1 Macbook, that's why pulled image could not fit. Feel free to rebuild image.
```
docker pull takkat14/mlops-web-flask:latest
docker run -d -p 5001:5001 --name flask-app takkat14/mlops-web-flask:latest
```

That's all folks.


## How to run via docker-compose?
Prequisits: you need Docker :( Of course, you do

It's pretty simple:
```
docker-compose -f docker-compose.yaml up --build   
```
When you are done, just run `docker-compose down`.

## One more thing. 
Repo has workflows on pushes as well ;)
