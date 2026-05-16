from flask import Flask, render_template, request, jsonify, Response, stream_with_context
from flask_sqlalchemy import SQLAlchemy
from openai import OpenAI
import os
import json
from dotenv import load_dotenv

load_dotenv() 

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mydatabase.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

messages = [{"role": "system", "content": "你是一只精通JavaScript的猫娘,名字叫小七"}]

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)

class Visit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    count = db.Column(db.Integer, default=0)

@app.route('/')
def home():
    # visit = Visit.query.first()
    # visit.count += 1
    # db.session.commit()
    # return render_template('index.html', count=visit.count)
    return render_template('index.html')

@app.route('/ai')
def ai_page():
    return render_template('ai.html')

@app.route('/game')
def game_page():
    return render_template('cat_eat.html')

@app.route('/ai/api/chat', methods=['POST'])
def ai_chat():
    data = request.get_json()
    user_msg = data.get('message', '')

    if not user_msg:
        return jsonify({'reply': '请输入问题~'})
    
    api_key = os.getenv('DEEPSEEK_API_KEY')
    if not api_key:
        return jsonify({'reply': '未配置api_key'})

    reasoning_list = []
    reply_list = []
    reasoning = ''
    reply = ''

    def generate():
        message = {"role": "user", "content": user_msg}
        messages.append(message)
        client = OpenAI(api_key=api_key, base_url='https://api.deepseek.com')
        try:
            response = client.chat.completions.create(
                model="deepseek-v4-pro",
                messages=messages,
                stream=True,
                reasoning_effort="high",
                extra_body={"thinking": {"type": "enabled"}}
            )
            yield "data: {\"type\": \"start\"}\n\n"

            for chunk in response:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    # 提取内容片段
                    if hasattr(delta, 'content') and delta.content:
                        event_data = json.dumps({"type": "content", "content": delta.content})
                        reply_list.append(delta.content)
                        yield f"data: {event_data}\n\n"
                    # 提取思考片段
                    if hasattr(delta, 'reasoning_content') and delta.reasoning_content:
                        event_data = json.dumps({"type": "reasoning", "content": delta.reasoning_content})
                        reasoning_list.append(delta.reasoning_content)
                        yield f"data: {event_data}\n\n"
            yield "data: {\"type\": \"end\"}\n\n"

            reasoning = ''.join(reasoning_list)
            reply = ''.join(reply_list)

            #加入本次消息回复
            message = {
                "role": "assistant",
                "content": reply
            }
            if reasoning:
                message['reasoning_content'] = reasoning
            messages.append(message)
            # print(messages)

        except Exception as e:
            error_data = json.dumps({"type": "error", "message": str(e)})
            yield f"data: {error_data}\n\n"

    # 使用 stream_with_context 可以确保在客户端断开连接时，生成器也能正确关闭
    return Response(stream_with_context(generate()), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
