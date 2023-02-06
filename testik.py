from configurator import get_config
from api.src.trainer import ModelTrainer
from api.src.data_preproccesor import get_train_test_data
import bson

cfg = get_config()

__type = "linearSVC"
__params = {"C": 0.5}

classname = cfg[__type].model
vectorizer = cfg[__type].tfidf

model_trainer = ModelTrainer(classname, vectorizer,
                             model_params=__params,
                             load_model=False,
                             model_path=None,
                             common_cfg=cfg,
                             )
# X_train, X_test, y_train, y_test = get_train_test_data(cfg)

# print(X_train.shape, y_train.shape)
# print(X_test.shape, y_test.shape)

# print(model_trainer.get_model())
# model_trainer.fit(X_train.values, y_train)
print(bson.ObjectId())