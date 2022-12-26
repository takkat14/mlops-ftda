from flask import Flask
import data.data_preproccesor as dl
import os

app = Flask(__name__)

@app.route("/")
def hello():
    return "<h1 style='color:blue'>Hello There!</h1>"


@app.route("/download")
def testing_download():
    dl.DataProcessor.download()


@app.route("/models/list")
def list_available_models():
    pass


@app.route("/models/add")
def train():
    # train
    # add model to config
    return



if __name__ == "__main__":
    app.run(host='0.0.0.0',port=5001)