from flask import Flask
from flask import request, jsonify
from DatabaseAccessor import DBAccessor
from flask_cors import CORS
app = Flask(__name__)
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})
db_accessor = DBAccessor()


@app.route('/')
def hello_world():
    return 'hello,world'


@app.route('/api/query_movie_list', methods=['POST'])
def query_movie_list():
    start_from = request.json.get('start_from')
    limitation = request.json.get('limitation')
    search_key = request.json.get('search_key')
    if search_key == '' or (not search_key):
        search_key = '%'
    else:
        search_key = "%" + search_key + "%"
    return jsonify(DBAccessor.get_dict(db_accessor.query_movie_list(start_from, limitation, search_key)))


@app.route('/api/query_movie/<int:movie_id>', methods=['POST'])
def query_movie(movie_id):
    return jsonify(DBAccessor.get_dict(db_accessor.query_movie(movie_id)))


@app.route('/api/query_order_list', methods=['POST'])
def query_order_list():
    start_from = request.json.get('start_from')
    limitation = request.json.get('limitation')
    time_limitation = request.json.get('time_limitation')
    if time_limitation == '' or (not time_limitation):
        time_limitation = '%'
    return jsonify(DBAccessor.get_dict(db_accessor.query_order_list(start_from, limitation, time_limitation)))


@app.route('/api/insert_order', methods=['POST'])
def insert_order():
    item = request.json.get('item')
    db_accessor.insert_order(item)
    return "success", 200


@app.route('/api/recommend_movie_list', methods=['POST'])
def recommend_movie_list():
    start_from = request.json.get('start_from')
    limitation = request.json.get('limitation')
    return jsonify(DBAccessor.get_dict(db_accessor.query_recommend_movie_list(start_from, limitation)))


if __name__ == '__main__':
    app.run('0.0.0.0', 12450)
