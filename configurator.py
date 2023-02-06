from hydra import initialize, compose


def get_config():
    initialize(version_base=None, config_path="./configs")
    cfg = compose("config.yaml")
    print(cfg)
    return cfg

