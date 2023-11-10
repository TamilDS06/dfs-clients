from flask import render_template, request, redirect, url_for, session, flash, get_flashed_messages
import boto3
import os
import mimetypes
import atexit
# from constant import Constant
from dbmodels import app, User, FileMetadata, db, bcrypt
from dotenv import dotenv_values

dot_env_values = dotenv_values()
AWS_ACCESS_KEY_ID = dot_env_values["AWS_ACCESS_KEY_ID"]
AWS_SECRET_ACCESS_KEY = dot_env_values["AWS_SECRET_ACCESS_KEY"]
AWS_REGION = dot_env_values["AWS_REGION"]
S3_BUCKET_NAME = dot_env_values["S3_BUCKET_NAME"]

s3_client = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name=AWS_REGION)


@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    user_folder = f"user_{user_id}/"

    # To List metadata for objects owned by the logged-in user
    file_metadata_list = FileMetadata.query.filter_by(client_name=user_folder).all()

    return render_template('index.html', file_metadata_list=file_metadata_list)

@app.route('/upload', methods=['POST'])
def upload():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    user_folder = f"user_{user_id}/"

    if 'file' not in request.files:
        return redirect('/')

    file = request.files['file']
    if file.filename == '':
        return redirect('/')

    object_key = os.path.join(user_folder, file.filename)
    s3_client.upload_fileobj(file, S3_BUCKET_NAME, object_key)

    file_type, _ = mimetypes.guess_type(file.filename)
    # To Create a metadata entry for the uploaded file
    file_metadata = FileMetadata(
        client_name=user_folder,
        file_name=file.filename,
        file_type=file_type or "unknown",
        url_link_s3=f"https://{S3_BUCKET_NAME}.s3.amazonaws.com/{object_key}"
    )
    db.session.add(file_metadata)
    db.session.commit()

    return redirect('/')

@app.route('/delete/<object_key>')
def delete(object_key):
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    user_folder = f"user_{user_id}/"
    object_key_s3 = os.path.join(user_folder, object_key)
    

    s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=object_key_s3)

    # To Delete the metadata entry for the deleted file
    file_metadata = FileMetadata.query.filter_by(client_name=user_folder, file_name=object_key).first()
    if file_metadata:
        db.session.delete(file_metadata)
        db.session.commit()

    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        return redirect('/login')
    return render_template('register.html')

@app.route('/download/<object_key>')
def download(object_key):
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    user_folder = f"user_{user_id}/"
    object_key = os.path.join(user_folder, object_key)

    # To Generate a pre-signed URL for downloading the S3 object
    url = s3_client.generate_presigned_url(
        'get_object',
        Params={'Bucket': S3_BUCKET_NAME, 'Key': object_key},
        ExpiresIn=3600  # URL expires in 1 hour
    )

    return url

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect('/')
        else:
            flash('Invalid username or password. Please try again.', 'warning')
            return redirect('/login')

    return render_template('login.html', messages=get_flashed_messages())

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('user_id', None)
    return redirect('/login')

def logout_on_shutdown():
    # To Perform logout action when the server is stopped
    if 'user_id' in session:
        session.pop('user_id', None)

atexit.register(logout_on_shutdown)


if __name__ == '__main__':
    app.run(host=dot_env_values['host'], port=dot_env_values['port'], debug=dot_env_values['debug'])
