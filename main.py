from flask import Flask, render_template, request, redirect, url_for, session, flash, get_flashed_messages
import boto3
import os
import mimetypes
import atexit
# from constant import Constant
# from dbmodels import app, User, FileMetadata, db, bcrypt
from dotenv import dotenv_values
import pandas as pd
from utilss import *

app = Flask(__name__)

# AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
# AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
# AWS_REGION = os.environ.get("AWS_REGION")
# S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME")
HOST = os.environ.get("HOST")
PORT = os.environ.get("PORT")
DEBUG = os.environ.get("DEBUG")

app.config['SECRET_KEY'] = 'your_secret_key'  # Change to a strong secret key

# USERS_CSV_PATH = 'C:\\my_folder\\dfs_python_flask_aws\\csv_files\\FileMetaData.csv'
# METADATA_CSV_PATH = 'C:\\my_folder\\dfs_python_flask_aws\\csv_files\\user_data.csv'

# # Initialize or read existing CSV files
users_df = read_csv(USERS_CSV_PATH)
metadata_df = read_csv(METADATA_CSV_PATH)


# Create the initial CSV files if they don't exist
if users_df.empty:
    users_df = pd.DataFrame(columns=['username', 'password'])
    write_csv(users_df, USERS_CSV_PATH)

if metadata_df.empty:
    metadata_df = pd.DataFrame(columns=['client_name', 'file_name', 'file_type', 'url_link_s3', 'created_time', 'updated_time'])
    write_csv(metadata_df, METADATA_CSV_PATH)

# s3_client = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name=AWS_REGION)


@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    # user_folder = f"user_{user_id}/"

    # To List metadata for objects owned by the logged-in user
    # file_metadata_list = FileMetadata.query.filter_by(client_name=user_folder).all()
    metadata_df = read_csv(METADATA_CSV_PATH)
    # # file_metadata_list = []
    file_metadata = metadata_df[metadata_df['client_name'] == user_id].values.tolist()

    return render_template('index.html', file_metadata_list=file_metadata)

@app.route('/upload', methods=['POST'])
def upload():
#     if 'user_id' not in session:
#         return redirect('/login')

#     user_id = session['user_id']
#     user_folder = f"user_{user_id}/"

#     if 'file' not in request.files:
#         return redirect('/')

#     file = request.files['file']
#     if file.filename == '':
#         return redirect('/')

#     object_key = os.path.join(user_folder, file.filename)
#     s3_client.upload_fileobj(file, S3_BUCKET_NAME, object_key)

#     file_type, _ = mimetypes.guess_type(file.filename)
#     # To Create a metadata entry for the uploaded file
#     file_metadata = FileMetadata(
#         client_name=user_folder,
#         file_name=file.filename,
#         file_type=file_type or "unknown",
#         url_link_s3=f"https://{S3_BUCKET_NAME}.s3.amazonaws.com/{object_key}"
#     )
#     db.session.add(file_metadata)
#     db.session.commit()

#     return redirect('/')
    if 'user_id' not in session:
        flash('You need to log in to upload files.', 'warning')
        return redirect('/login')

    user_id = session['user_id']
    file = request.files['file']
    file_path = request.form.get('file_path')
    file_type, _ = mimetypes.guess_type(file.filename)

    if file and allowed_file(file.filename):
        # Save the file to S3 and get the URL
        file_url = upload_file_to_s3(file, user_id, file_path)

        # Record file metadata in the DataFrame
        metadata_dff = pd.read_csv(METADATA_CSV_PATH)
        record_file_metadata(user_id, file.filename, file_type, file_url, metadata_dff)

        flash('File uploaded successfully!', 'success')
    else:
        flash('Invalid file format. Please upload a valid file.', 'warning')

    return redirect('/')

@app.route('/delete/<object_key>')
def delete(object_key):
#     if 'user_id' not in session:
#         return redirect('/login')

#     user_id = session['user_id']
#     user_folder = f"user_{user_id}/"
#     object_key_s3 = os.path.join(user_folder, object_key)
    

#     s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=object_key_s3)

#     # To Delete the metadata entry for the deleted file
#     file_metadata = FileMetadata.query.filter_by(client_name=user_folder, file_name=object_key).first()
#     if file_metadata:
#         db.session.delete(file_metadata)
#         db.session.commit()

#     return redirect(url_for('index'))
    if 'user_id' not in session:
        flash('You need to log in to delete files.', 'warning')
        return redirect('/login')

    user_id = session['user_id']

    # Delete file from S3
    delete_file_from_s3(object_key, user_id)

    # Delete file metadata from DataFrame
    metadata_dff = read_csv(METADATA_CSV_PATH)
    delete_file_metadata(user_id, object_key, metadata_dff)

    flash(f'File {object_key} deleted successfully!', 'success')
    return redirect('/')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        # user = User(username=username, password=hashed_password)
        
        # db.session.add(user)
        # db.session.commit()
        # return redirect('/login')
        if username_exists(username, users_df):
            flash('Username already exists. Please choose a different username.', 'warning')
        else:
            create_user(username, password, users_df)
            flash('Registration successful! You can now log in.', 'success')
            return redirect('/login')

    return render_template('register.html', messages=get_flashed_messages())
    # return render_template('register.html')

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
    #     # user = User.query.filter_by(username=username).first()
    #     user = users_df[0]

    #     if user and bcrypt.check_password_hash(user.password, password):
    #         session['user_id'] = user.id
    #         return redirect('/')
    #     else:
    #         flash('Invalid username or password. Please try again.', 'warning')
    #         return redirect('/login')

    # return render_template('login.html', messages=get_flashed_messages())
        users_dff = pd.read_csv(USERS_CSV_PATH)
        user = authenticate_user(username, password, users_dff)

        if user:
            session['user_id'] = user.username
            flash('Login successful!', 'success')
            return redirect('/')
        else:
            flash('Invalid username or password. Please try again.', 'warning')

    return render_template('login.html', messages=get_flashed_messages())

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    # session.pop('user_id', None)
    # return redirect('/login')
    if 'user_id' in session:
        session.pop('user_id', None)
        flash('Logout successful!', 'success')
    return redirect('/')

def logout_on_shutdown():
    # To Perform logout action when the server is stopped
    if 'user_id' in session:
        session.pop('user_id', None)

atexit.register(logout_on_shutdown)


if __name__ == '__main__':
    app.run(host=HOST, port=PORT, debug=DEBUG)
