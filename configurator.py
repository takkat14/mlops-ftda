from hydra import initialize, compose
import os


def get_config():
    initialize(version_base=None, config_path="./configs")
    cfg = compose("config.yaml")
    if os.getenv("RUNTIME_DC"):
        cfg.minio.host = os.environ["MINIO_HOST"]
        cfg.mongo.host = os.environ["MONGO_HOST"]
    return cfg
