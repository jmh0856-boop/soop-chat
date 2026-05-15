from flask import Flask, render_template, request, jsonify
from chat_collector import add_streamer, remove_streamer, active_streamers, start
from storage import storage

app = Flask(__name__)

# 서버 시작할 때 채팅 수집기도 같이 시작
start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_streamer', methods=['POST'])
def api_add_streamer():
    data = request.json
    streamer_id = data.get('streamer_id', '').strip()
    if not streamer_id:
        return jsonify({'success': False, 'message': '스트리머 ID를 입력해주세요'})
    message = add_streamer(streamer_id)
    return jsonify({'success': True, 'message': message})

@app.route('/remove_streamer', methods=['POST'])
def api_remove_streamer():
    data = request.json
    streamer_id = data.get('streamer_id', '').strip()
    message = remove_streamer(streamer_id)
    return jsonify({'success': True, 'message': message})

@app.route('/streamers')
def api_streamers():
    return jsonify({'streamers': list(active_streamers)})

@app.route('/search')
def api_search():
    streamer_id = request.args.get('streamer_id', '')
    nickname = request.args.get('nickname', '')
    if not streamer_id or not nickname:
        return jsonify({'chats': []})
    chats = storage.search_by_nickname(streamer_id, nickname)
    return jsonify({'chats': chats})

@app.route('/all_chats')
def api_all_chats():
    streamer_id = request.args.get('streamer_id', '')
    if not streamer_id:
        return jsonify({'chats': []})
    chats = storage.get_all_chats(streamer_id)
    return jsonify({'chats': chats})

if __name__ == '__main__':
    app.run(debug=True)