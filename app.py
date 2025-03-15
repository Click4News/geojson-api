# app.py
from flask import Flask

app = Flask(__name__)

@app.route("/")
def hello_world():
    return "Hello, AWS CodePipeline + Flask!"

if __name__ == "__main__":
    # Flask 預設在 localhost:5000 監聽
    # 若要在 EC2/Elastic Beanstalk 上執行，需要改成 0.0.0.0 並使用指定 port
    # 例如: app.run(host='0.0.0.0', port=8080)
    app.run(host='0.0.0.0', port=5000)
