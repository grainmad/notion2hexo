from flask import Flask, render_template, request, redirect, url_for
from dotenv import load_dotenv
import os
import blog_copy_replace_file
app = Flask(__name__, static_folder="uploads", static_url_path="/uploads")

# 在这里设置你的密钥
SECRET_KEY = os.getenv("SECRET_KEY")
load_dotenv()

# 上传文件的页面
@app.route('/')
def upload_form():
    return render_template('upload.html')

# 处理文件上传
@app.route('/', methods=['POST'])
def upload_file():
    uploaded_file = request.files['file']
    if uploaded_file and allowed_file(uploaded_file.filename) and request.form.get('key') == SECRET_KEY:
        # 这里可以设置文件保存的路径，例如保存在当前目录下的 uploads 文件夹中
        uploaded_file.save('uploads/' + uploaded_file.filename)
        blog_copy_replace_file.process("uploads", uploaded_file.filename)
        return redirect(url_for('upload_success'))
    else:
        return render_template('upload.html', error='Invalid file or key')

# 定义允许上传的文件类型
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'zip'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 上传成功页面
@app.route('/success')
def upload_success():
    return 'File uploaded successfully!'

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)
