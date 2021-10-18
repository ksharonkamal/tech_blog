from datetime import datetime, timedelta
import jwt
from app import app
import os
from flask import request, jsonify
from app.models_and_views.models import User
from functools import wraps
#from sqlalchemy import db
def deserialize_to_json(user_data):
    return {"user_id":user_data.id,"user_name":user_data.name,"email":user_data.email,"mobile":user_data.mobile,"technology":user_data.technology}


def encode_auth_token(user):
    """
    Generates the Auth Token
    :return: string
    """
    try:
        payload = {
            'exp': datetime.utcnow() + timedelta(days=1, seconds=0),
            'iat': datetime.utcnow(),
            'sub': deserialize_to_json(user)
        }
        return jwt.encode(
            payload,
            app.config.get('SECRET_KEY'),
            algorithm='HS256'
        )
    except Exception as e:
        return e


def decode_auth_token(auth_token):
    """
    Decodes the auth token
    :param auth_token:
    :return: integer|string
    """
    try:
        payload = jwt.decode(auth_token, app.config.get('SECRET_KEY'))
        return True, payload['sub']
    except jwt.ExpiredSignatureError:
        return False, 'Signature expired. Please log in again.'
    except jwt.InvalidTokenError:
        return False, 'Invalid token. Please log in again.'


def authentication(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        token = None
        print(request.headers.get('token'))
        # if 'x-access-token' in request.headers:
        #     token = request.headers['x-access-token']
        # is_valid, token = decode_auth_token(str(request.headers.get('token')))
        try:
            is_valid, token = decode_auth_token(request.headers['token'])
        except:
            return jsonify(status=404,message="Token required")
        if is_valid:
            return func(*args, **kwargs)
        return jsonify(status=401,message=token)
    return decorated




# def is_admin_or_superadmin(func):
#     @wraps(func)
#     def decorated(*args, **kwargs):
#         data=request.get_json()
#         user_id=data.get('user_id')
#         try:
#             check_admin=User.objects.filter(id=user_id).first()
#         except Exception as e:
#             return jsonify(status=400,message="User not found")
#         if (check_admin.roles==2) or (check_admin.roles==3):
#             return func(*args, **kwargs)
#         return jsonify(status=401,message="Permissions denied")
#     return decorated
