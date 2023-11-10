import os
import pandas as pd
from dbmodels import *
from datetime import datetime
import boto3
from flask_bcrypt import Bcrypt

current_script_directory = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(current_script_directory, '..'))
METADATA_CSV_PATH= project_root+"\\dfs_python_flask_aws\\csv_files\\FileMetaData.csv"
USERS_CSV_PATH = project_root+"\\dfs_python_flask_aws\\csv_files\\user_data.csv"
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.environ.get("AWS_REGION")
S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME")
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
s3_client = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name=AWS_REGION)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def upload_file_to_s3(file, client_name, file_path):
    # Simulate S3 upload and generate a file URL
    # In a real scenario, you would use boto3 to upload to AWS S3
    # This is a placeholder for demonstration purposes
    object_key = os.path.join(client_name, file.filename)
    s3_client.upload_fileobj(file, S3_BUCKET_NAME, object_key)
    s3_file_url = f'https://s3.amazonaws.com/{client_name}/{file.filename}'
    return s3_file_url


def delete_file_from_s3(file_name, client_name):
    # Simulate S3 file deletion
    # In a real scenario, you would use boto3 to delete the file from AWS S3
    # This is a placeholder for demonstration purposes
    print(f'Deleting file {file_name} from S3 for client {client_name}')
    # Actual deletion logic using boto3 goes here
    object_key_s3 = os.path.join(client_name, file_name)
    s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=object_key_s3)


def get_file_type(filename):
    file_extension = filename.rsplit('.', 1)[1].lower()
    if file_extension in {'txt', 'pdf'}:
        return 'Document'
    elif file_extension in {'png', 'jpg', 'jpeg', 'gif'}:
        return 'Image'
    else:
        return 'Other'


# Helper function to read CSV files
def read_csv(file_path):
    if os.path.exists(file_path):
        return pd.read_csv(file_path)
    else:
        return pd.DataFrame()


# Helper function to write DataFrame to CSV file
def write_csv(data_frame, file_path):
    data_frame.to_csv(file_path, index=False)


# Helper function to get user files based on client_name
def get_user_files(client_name):
    return metadata_df[metadata_df['client_name'] == client_name].to_dict(orient='records')

# Helper function to authenticate a user
def authenticate_user(username, password, users_df):
    user = users_df[(users_df['username'] == username) & (users_df['password'] == password)]
    if not user.empty:
        return User(username=user['username'].values[0], password=user['password'].values[0])
    return None

# Helper function to check if a username already exists
def username_exists(username, users_df):
    return not users_df[users_df['username'] == username].empty

# Helper function to create a new user
def create_user(username, password, users_df):
    new_user = User(username=username, password=password)
    users_df = pd.concat([users_df, pd.DataFrame([new_user.__dict__])], ignore_index=True)
    write_csv(users_df, USERS_CSV_PATH)

# Helper function to record file metadata in DataFrame
def record_file_metadata(client_name, file_name, file_type, url_link_s3, metadata_dff):
    created_time = updated_time = datetime.utcnow()
    new_metadata = FileMetadata(client_name=client_name, file_name=file_name, file_type=file_type, url_link_s3=url_link_s3, created_time=created_time, updated_time=updated_time)
    metadata_df = pd.concat([metadata_dff, pd.DataFrame([new_metadata.__dict__])], ignore_index=True)
    write_csv(metadata_df, METADATA_CSV_PATH)

# Helper function to delete file metadata from DataFrame
def delete_file_metadata(client_name, file_name, metadata_dff):
    global metadata_df
    metadata_df = metadata_dff[~((metadata_dff['client_name'] == client_name) & (metadata_dff['file_name'] == file_name))]
    write_csv(metadata_df, METADATA_CSV_PATH)
