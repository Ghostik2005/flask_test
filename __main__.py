#coding: utf-8

import flask
import library.api as app_api


app = flask.Flask(__name__)


methods = app_api.API()


@app.route('/get_load/', methods=['GET', 'POST'])
def get_load():
    if flask.request.method == 'POST':
        json_data = flask.request.json
        return flask.jsonify(methods.get_post_load(json_data))
    else:
        return methods.get_get_load()


@app.route('/get_history/', methods=['GET'])
def get_history():
    return flask.jsonify(methods.get_history())


@app.route('/clear/', methods=['POST'])
def clear():
    json_data = flask.request.json
    return flask.jsonify(methods.clear(json_data))

@app.route('/', methods=['GET', 'POST'])
def help():
    msg = []
    msg.append('GET /get_history возвращает историю запросов')
    msg.append('GET  /get_load  возвращает значение нагрузок в строке')
    msg.append("POST  /get_load  возвращает значение нугрузок в JSON. Тип запрашиваемой нагрузки передается в JSON вида {'mem': True, 'cpu':True, 'gpu':True}")
    msg.append('POST  /clear  очистка хранилища')
    msg.append('    без параметров - полностью')
    msg.append("    параметры: {'start': 01:01:01:01:01, 'end':'02:02:02:02:02'}")
    msg.append('    start - начало диапазона уделения, необязательный параметр')
    msg.append('    end - конец диапазона уделения, необязательный параметр')
    return '<br>'.join(msg)



###############################################

if "__main__" == __name__:
    app.debug = not True
    app.run(host='0.0.0.0', port=19999)

