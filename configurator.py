from hydra import initialize, compose
import os


def get_config():
    initialize(version_base=None, config_path="./configs")
    cfg = compose("config.yaml")
    if os.environ["RUNTIME_DOCKER"]:
        cfg.minio.host = os.environ["MINIO_HOST"]
        cfg.mongo.host = os.environ["MONGO_HOST"]
    return cfg
