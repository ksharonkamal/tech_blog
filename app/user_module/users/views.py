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
from app.models_and_views.pagination import get_paginated_list
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
        user=db.session.query(User).filter(or_(User.email == email, User.mobile == mobile)).first()
        if user:
            if check_password_hash(user.password,password):
                token = encode_auth_token(user)
                app.logger.info(token)
                response=user_serializer(user)
                app.logger.info(f'{user.name} Logged in successfully')
                return jsonify(status=200,data=response,message="Logged in successfully", token=token.decode('UTF-8'))
            else:
                app.logger.info(f"{user.name} Incorrect password")
                return jsonify(status=404,messsage="Incorrect password")
        else:
            app.logger.info(f"user not found")
            return jsonify(status=404,message="user not found")


class Logout(Resource):
    def post(self):
        app.logger.info("Logged out successfully")
        return jsonify(status=200, message="Logged out successfully")

    def get(self):
        app.logger.info("Logged out successfully")
        return jsonify(status=200, message="Logged out successfully")


class Register(Resource):
    def post(self):
        data = request.get_json()
        name = data.get('name')
        email = data.get('email')
        mobile = data.get('mobile')
        list_of_tech = data.get('technology')
        password = data.get("password")

        # check all data exists or not
        if not (name and email and mobile and list_of_tech and password):
            msg = 'name, email, mobile, technology and password are required fields'
        # check valid email
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address'
        elif not (re.match(r'[0-9]+', mobile) and len(mobile) == 10):
            msg = 'Invalid phone number'
        # check valid name
        elif not re.match(r'[A-Za-z0-9]+', name):
            msg = 'Name must contain only charachners and numbers'
        elif not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!#%*?&]{6,20}$', password):
            msg = 'Password should contain min 8 characters, a special character, Uppercase, lowercase and a number'
        # check user already exist
        else:
            try:
                user = db.session.query(User).filter(or_(User.email == email,
                                                         User.mobile == mobile,
                                                         User.name == name)).first()
                if user:
                    msg = 'User already exist'
                else:
                    ids_list = f"{replace_with_ids(list_of_tech)}"

                    print(ids_list)

                    # technology = ast.literal_eval(technology)
                    today = datetime.now()
                    date_time_obj = today.strftime('%Y/%m/%d %H:%M:%S')
                    print(date_time_obj)
                    password = generate_password_hash(password, method='sha256')
                    user = User(name, email, mobile, ids_list, password, date_time_obj, date_time_obj)

                    db.session.add(user)
                    db.session.commit()

                    response = {"name": name, "email": email, "mobile": mobile, "technology": list_of_tech}
                    app.logger.info(f'{user.name} Registered successfully')
                    return jsonify(status=200, data=response, message="Registered successfully")
            except:
                app.logger.info("Database connection not established")
                return jsonify(status=404, message="Database connection not established")
        app.logger.info(msg)
        return jsonify(status=400, message=msg)


class UpdatePassword(Resource):
    @authentication
    def put(self):
        data = request.get_json() or {}
        email = data.get("email")
        mobile = data.get("mobile")
        old_password = data.get("old_password")
        new_password = data.get("new_password")
        confirm_new_password = data.get("confirm_new_password")

        if not ((email or mobile) and (old_password and new_password and confirm_new_password)):
            app.logger.info(f'email (or) mobile , old_password, new_password and confirm_new_password required')
            return jsonify(status=400,
                           message="email (or) mobile , old_password, new_password and confirm_new_password required")
        try:
            user = db.session.query(User).filter(or_(User.email == email, User.mobile == mobile)).first()
            if user:
                if check_password_hash(user.password, data.get('old_password')):
                    if new_password == confirm_new_password:
                        if new_password == old_password:
                            app.logger.info("New password and old password should not be same")
                            return jsonify(status=400, message="New password and old password should not be same")
                        if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!#%*?&]{6,20}$',
                                        new_password):
                            app.logger.info(
                                "Password should contain min 8 characters, a special character, Uppercase, lowercase and a number")
                            return jsonify(status=400,
                                           message='Password should contain min 8 characters, a special character, Uppercase, lowercase and a number')
                        user.password = generate_password_hash(new_password, method='sha256')
                        db.session.commit()
                        app.logger.info(f'{user.name} Password updated successfully')
                        return jsonify(status=200, message="Password updated successfully")
                    else:
                        app.logger.info(f'{user.name} New password and confirm new password doesnt match')
                        return jsonify(status=200, message="New password and confirm new password doesn't match")
                else:
                    app.logger.info(f"{user.name} Incorrect old password")
                    return jsonify(status=404, message="Incorrect old password")
            else:
                app.logger.info("User not found")
                return jsonify(status=404, message="User not found")
        except:
            app.logger.info("Unknown database")
            return jsonify(status=404, message="Unknown database")


class ForgotPassword(Resource):
    def post(self):
        data = request.get_json()
        email = data.get("email")
        mobile = data.get("mobile")

        if not (email and mobile):
            app.logger.info("email, mobile fields are required")
            return jsonify(status=400, message="email, mobile fields are required")
        else:
            try:
                user = db.session.query(User).filter(and_(User.email == email, User.mobile == mobile)).first()
                if user:
                    new_password = send_mail_to_reset_password(user.email, user.name)
                    if new_password == 'Error':
                        app.logger.info("mail sending failed")
                        return jsonify(status=400, message="mail sending failed")
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


class UserProfile(Resource):
    def put(self):
        data = request.get_json() or {}
        try:
            user_id = data.get('user_id')
            user_update = db.session.query(User).filter_by(id=user_id).first()
        except:
            app.logger.info("User not found")
            return jsonify(status=404, message="user not found")

        name = data.get('name')
        technology = data.get('technology')

        if not (name and technology and user_id):
            app.logger.info("name,email,mobile,technology and user_id are required")
            return jsonify(status=400, message="name,email,mobile,technology and user_id are required")

        elif not re.match(r'[A-Za-z0-9]+', name):
            msg = 'name must contain only characters and numbers'
            app.logger.info(msg)
            return jsonify(status=404, message=msg)
        else:
            if user_update:
                if not user_update.name == name:
                    user_update.name = name
                ids_list = f"{replace_with_ids(technology)}"
                user_update.technology = ids_list
                today = datetime.now()
                user_update.date_time_obj = today.strftime('%Y/%m/%d %H:%M:%S')
                db.session.commit()
                response = {"name": user_update.name, "technology": technology}
                app.logger.info(f'{user_update.name} Updated successfully')
                return jsonify(status=200, data=response, message="updated Successfully")

        #    except:
        #         app.logger.info("database not established")
        #         return jsonify(status=404, message="database not established")


class GetProfile(Resource):
    def get(self,user_id):
        user_data=db.session.query(User).filter_by(id=user_id).first()
        if not user_data:
            app.logger.info("user not found")
            return jsonify(status=400, message="user not found")
        return jsonify(status=200,data=user_serializer(user_data),message="user data")
