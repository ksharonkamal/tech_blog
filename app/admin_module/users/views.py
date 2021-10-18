from flask import jsonify, request
from sqlalchemy.future import select
from sqlalchemy.sql import or_
from flask_restplus import Resource
from datetime import datetime
from sqlalchemy.orm import query
from sqlalchemy.sql.expression import delete
from sqlalchemy.sql.functions import user
from werkzeug.security import generate_password_hash, check_password_hash
from app.models_and_views.models import User, Technologies, Queries, Comments, LikesDislikes
from app import app, db
from sqlalchemy import or_,and_,desc
import re,ast
from app.authentication import encode_auth_token,authentication
#is_admin_or_superadmin
from app.models_and_views.serializer import query_serializer,comments_serializer, user_serializer,replace_with_ids,technology_serializer
from utils.pagination import get_paginated_list
from utils.smtp_mail import send_mail_to_reset_password


class Login(Resource):
    def post(self):
        data = request.get_json() or {}
        if not data:
            app.logger.info("No input(s)")
            return jsonify(status=400, message="No input(s)")
        email=data.get("email")
        mobile=data.get("mobile")
        password=data.get('password')
        if not ((email or mobile) and password):
            app.logger.info("email or mobile and password are required")
            return jsonify(status=400,message="email or mobile and password are required")
        user = db.session.query(User).filter(or_(User.email == email, User.mobile == mobile)).first()
        if user:
            if user.role == 2 or user.role == 3 :
                if check_password_hash(user.password, password):
                    token = encode_auth_token(user)
                    app.logger.info(token)
                    response = user_serializer(user)
                    app.logger.info(f'{user.name} Logged in successfully')
                    return jsonify(status=200, data=response, message="Logged in successfully",
                                   token=token.decode('UTF-8'))
                else:
                    app.logger.info(f"{user.name} Incorrect password")
                    return jsonify(status=404, messsage="Incorrect password")
            else:
                app.logger.info(f"{user.name} Not allowed to login as admin")
                return jsonify(status=404,messsage="Not allowed to login as admin")
        else:
            app.logger.info(f"user not found")
            return jsonify(status=404,message="user not found")


class ForgotPassword(Resource):
    def post(self):
        data = request.get_json()
        email = data.get("email")
        mobile = data.get("mobile")

        if not (email and mobile):
            app.logger.info("email, mobile fields are required")
            return jsonify(status=400,message="email, mobile fields are required")
        else:
            try:
                user = db.session.query(User).filter(and_(User.email == email, User.mobile == mobile)).first()
                if user:
                    new_password = send_mail_to_reset_password(user.email, user.name)
                    if new_password == 'Error':
                        app.logger.info("mail sending failed")
                        return jsonify(status=400,message="mail sending failed")
                    app.logger.info("Email sent successfully")
                    today = datetime.now()
                    date_time_obj = today.strftime('%Y/%m/%d %H:%M:%S')
                    user.updated_at = date_time_obj
                    user.password = generate_password_hash(new_password, method='sha256')
                    db.session.commit()
                    app.logger.info(f'{user.name} password changed  successfully')
                    return jsonify(status=200, message="password changed  successfully")
                app.logger.info("cannot change password")
                return jsonify(status=400, message="cannot change password")
            except:
                app.logger.info("database error")
                return jsonify(status=400, message="database error")


class UserStatus(Resource):
    # @authentication
    def put(self):
        data = request.get_json() or {}
        if not data:
            app.logger.info("No input(s)")
            return jsonify(status=400, message="No input(s)")
        user_id = data.get('user_id')
        change_user_id = data.get('change_user_id')
        change_user_role = data.get('change_user_role')
        if not (change_user_id and user_id and change_user_role):
            app.logger.info("change_user_id and user id and change_user_role are required fields")
            return jsonify(status=404, message="change_user_id and user id and change_user_role are required fields")
        user_check = db.session.query(User).filter_by(id=user_id).first()
        if not user_check:
            app.logger.info("User not found")
            return jsonify(status=400, message="User not found")
        change_user_role_check = db.session.query(User).filter_by(id=change_user_id).first()
        if not change_user_role:
            app.logger.info("User you wanted to change role not found")
            return jsonify(status=400, message="User you wanted to change role not found")

        if user_check.roles == 2:
            change_user_role_check.roles = change_user_role
            today = datetime.now()
            date_time_obj = today.strftime('%Y/%m/%d %H:%M:%S')
            change_user_role_check.updated_at = date_time_obj
            db.session.commit()
            app.logger.info(f"{change_user_role_check.name} role changed successfully")
            return jsonify(status=200, message=f"{change_user_role_check.name} role changed successfully")
        app.logger.info("User not allowed to perform this action")
        return jsonify(status=404, message="User not allowed to perform this action")


class UserDelete(Resource):
    # @authentication
    def delete(self):
        data = request.get_json() or {}
        if not data:
            app.logger.info("No input(s)")
            return jsonify(status=400, message="No input(s)")
        user_id = data.get('user_id')
        delete_user = data.get('delete_user_id')
        if not (delete_user and user_id):
            app.logger.info("delete_user_id and User id are required fields")
            return jsonify(status=404, message="delete_user_id and User id are required fields")
        user_check = db.session.query(User).filter_by(id=user_id).first()
        if not user_check:
            app.logger.info("User not found")
            return jsonify(status=400, message="User not found")
        delete_user = db.session.query(User).filter_by(id=delete_user).first()
        if not delete_user:
            app.logger.info("User wanted to delete not found")
            return jsonify(status=400, message="User wanted to delete not found")

        if user_check.roles == 2 or user_check.roles == 3:
            delete_user.status = 0  # changed from roles to status (soft delete)
            today = datetime.now()
            date_time_obj = today.strftime('%Y/%m/%d %H:%M:%S')
            delete_user.updated_at = date_time_obj
            db.session.commit()
            app.logger.info(f"{delete_user} disabled successfully")
            return jsonify(status=200, message=f"{delete_user} disabled successfully")
        app.logger.info("User not allowed to perform this action")
        return jsonify(status=404, message="User not allowed to perform this action")


class GetProfile(Resource):
    def get(self,user_id):
        user_data=db.session.query(User).filter_by(id=user_id).first()
        if not user_data:
            app.logger.info("user not found")
            return jsonify(status=400, message="user not found")
        return jsonify(status=200,data=user_serializer(user_data),message="user data")


class GetAllUsers(Resource):
    def get(self):
        dt = {}
        users_list = []

        users = User.query.filter_by(roles=1).all()
        if not users:
            app.logger.info("No users in db")
            return jsonify(status=400, message="No users in db")
        for itr in users:
            dt = {
                'name': itr.name,
                'user_id': itr.id
            }
            users_list.append(dt)
            print(users_list)
        return jsonify(status=200, data=get_paginated_list(users_list, '/getallusers', start=request.args.get('start', 1),
                                                           limit=request.args.get('limit', 3)),
                       message="Returning all user's name and ids")
