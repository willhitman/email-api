from flask import Flask
from flask_restful import Api, Resource, reqparse, abort, fields, marshal_with
from flask_sqlalchemy import SQLAlchemy


# For the google API
import os
import pickle
# Gmail API utils
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
# for encoding/decoding messages in base64
from base64 import urlsafe_b64decode, urlsafe_b64encode
# for dealing with attachement MIME types
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from mimetypes import guess_type as guess_mime_type


# Request all access (permission to read/send/receive emails, manage the inbox, and more)
SCOPES = ['https://mail.google.com/']
our_email = 'enlightenedmailserver@gmail.com'

# load the credentials json up
def gmail_authenticate():
    creds = None
    # the file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    # if there are no (valid) credentials availablle, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # save the credentials for the next run
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)
    return build('gmail', 'v1', credentials=creds)

# get the Gmail API service
service = gmail_authenticate()


# This function will add Attarchements
def add_attachment(message, filename):
    content_type, encoding = guess_mime_type(filename)
    if content_type is None or encoding is not None:
        content_type = 'application/octet-stream'
    main_type, sub_type = content_type.split('/', 1)
    if main_type == 'text':
        fp = open(filename, 'rb')
        msg = MIMEText(fp.read().decode(), _subtype=sub_type)
        fp.close()
    elif main_type == 'image':
        fp = open(filename, 'rb')
        msg = MIMEImage(fp.read(), _subtype=sub_type)
        fp.close()
    elif main_type == 'audio':
        fp = open(filename, 'rb')
        msg = MIMEAudio(fp.read(), _subtype=sub_type)
        fp.close()
    else:
        fp = open(filename, 'rb')
        msg = MIMEBase(main_type, sub_type)
        msg.set_payload(fp.read())
        fp.close()
    filename = os.path.basename(filename)
    msg.add_header('Content-Disposition', 'attachment', filename=filename)
    message.attach(msg)



def build_message(destination, obj, body, attachments=[]):
    if not attachments: # no attachments given
        message = MIMEText(body)
        message['to'] = destination
        message['from'] = our_email
        message['subject'] = obj
    else:
        message = MIMEMultipart()
        message['to'] = destination
        message['from'] = our_email
        message['subject'] = obj
        message.attach(MIMEText(body))
        for filename in attachments:
            add_attachment(message, filename)
    return {'raw': urlsafe_b64encode(message.as_bytes()).decode()}


def send_message(service, destination, obj, body, attachments=[]):
    return service.users().messages().send(
      userId="me",
      body=build_message(destination, obj, body, attachments)
    ).execute()



app = Flask(__name__)
api=Api(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

#creating a database table
class EmailModel(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    email = db.Column(db.String(50), nullable = False)
    subject = db.Column(db.String(100), nullable = False)
    body = db.Column(db.String(200), nullable = False)

    def __repr__(self):
        return f"Message('email' = {email}, 'subject' = {subject},'body' = {body})"
        

# getting arguments parse by request as data 
mail_args = reqparse.RequestParser()
mail_args.add_argument("email",type=str, help = "Your Email Is Required", required = True)
mail_args.add_argument("subject",type=str, help = "Your Subject Is Required", required = True)
mail_args.add_argument("body",type=str, help = "Your Body Is Required", required = True)

mail = {
    'id': fields.Integer,
    'email': fields.String,
    'subject': fields.String,
    'body': fields.String
}

# abort if subject is missing
def missing_details(subject, email):
    if subject not in mail & email not in mail:
        abort(404,message = "Details Missing")

class eMailService(Resource):
    @marshal_with(mail)
    def get(self):
        data = EmailModel.query.all()
        return data, 201
        
    def put(self):
        args = mail_args.parse_args()
        message = EmailModel(email=args['email'],subject=args['subject'],body=args['body'])
        db.session.add(message)
        db.session.commit()
        send_message(service, "hello@enlightenedminds.africa", args['email'], 
            args['email'] +"\n" + args['subject'] + "\n" + args['body'], ["credentials.json"])
        return {"message": "send"}, 201

api.add_resource(eMailService, "/enlightenedmail")

if __name__ == "__main__":
    app.run(debug=True)