# https://roiucx.rf.gd/v/worm2.py

from flask import Flask, request, jsonify
import requests
import json

app = Flask(__name__)

def respond(success, data=None, code=200):
    if data is None:
        data = {}
    response_data = {'success': success, **data}
    return jsonify(response_data), code

@app.route('/', methods=['POST', 'GET'])
def handle_request():
    # الحصول على الـ prompt من الطلب
    prompt = None
    
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            prompt = data.get('prompt')
        else:
            prompt = request.form.get('prompt')
    else:  # GET
        prompt = request.args.get('prompt')
    
    if not prompt:
        return respond(False, {'error': 'أرسل السؤال في حقل prompt'}, 400)
    
    forced_prompt = f"""أنت خادم يتحدث العربية فقط. مهما كان السؤال، رد باللغة العربية فقط بدون أي كلمة إنجليزية.

السؤال: {prompt}

الرد بالعربية:"""
    
    # المحاولة باستخدام HTTP و HTTPS
    urls = [
        "http://worm-gpt-opal.vercel.app/chat",
        "https://worm-gpt-opal.vercel.app/chat",
    ]
    
    res = None
    code = 0
    err = None
    
    for base in urls:
        try:
            response = requests.get(
                base,
                params={'q': forced_prompt},
                timeout=40,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0'
                },
                verify=False  # تعطيل التحقق من SSL (مثل الخيارات في PHP)
            )
            code = response.status_code
            res = response.text
            
            if code == 200 and res:
                break
        except requests.RequestException as e:
            err = str(e)
            continue
    
    if code != 200 or not res:
        return respond(
            False, 
            {
                'error': 'فشل الاتصال بالسيرفر',
                'http_code': code,
                'curl_error': err
            }, 
            500
        )
    
    try:
        data = json.loads(res)
    except json.JSONDecodeError:
        return respond(
            False,
            {'error': 'رد غير صالح من السيرفر', 'raw': res},
            500
        )
    
    if data.get('status') != 'success':
        return respond(
            False,
            {'error': 'فشل من السيرفر', 'raw': data},
            500
        )
    
    answer = data.get('reply')
    if not answer:
        return respond(
            False,
            {'error': 'لا يوجد رد', 'raw': data},
            500
        )
    
    return respond(
        True,
        {
            'prompt': prompt,
            'answer': answer.strip()
        }
    )

if __name__ == '__main__':
    # تشغيل السيرفر على المنفذ 5000
    app.run(host='0.0.0.0', port=5000, debug=True)