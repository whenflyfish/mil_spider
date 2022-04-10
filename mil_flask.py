# 导入模板模块
from flask import Flask, jsonify, request
from flask_cors import CORS
from gevent.pywsgi import WSGIServer
from geventwebsocket.handler import WebSocketHandler
from mil_spider import ZGJSProcessor


# Flask相关变量声明
app = Flask(__name__)

app.config.update(
    DEBUG=True
)
# 跨域问题
CORS(app, supports_credentials=True)


@app.route('/mil', methods=["post", "get"])
def mil():
    # keys = request.form.get("key")  # 调用者传参 ky
    # 请求进来 输入爬取内容
    # taobao_details.get_detail(keys)#这里就是你的爬虫程序接入口
    # 爬虫程序
    myZGJScrawler = ZGJSProcessor()
    myZGJScrawler.crawler()
    return "mil_ok"  # jsonify({"code": 1})


@app.route('/mil/search', methods=["post", "get"])
def mil_keyword():
    keys = request.form.get("key")  # 调用者传参 ky
    # 请求进来 输入爬取内容
    # 爬虫程序
    myZGJScrawler = ZGJSProcessor()
    myZGJScrawler.crawler()
    return "mil_ok"  # jsonify({"code": 1})


if __name__ == '__main__':
    app.run(port=5555, debug=True, host='127.0.0.1')
    http_server = WSGIServer(('127.0.0.1', 5555), app, handler_class=WebSocketHandler)
    http_server.serve_forever()