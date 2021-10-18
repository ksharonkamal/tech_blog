from flask import jsonify, request
from sqlalchemy.future import select
from sqlalchemy.sql import or_
from flask_restplus import Resource
from datetime import datetime
from sqlalchemy.orm import query
from sqlalchemy.sql.expression import delete
from sqlalchemy.sql.functions import user
from werkzeug.security import generate_password_hash, check_password_hash
from app.models_and_views.models import User, Technologies, Queries, Comments, Opinion
from app import app, db
from sqlalchemy import or_,and_,desc
import re,ast
from app.authentication import encode_auth_token,authentication
#is_admin_or_superadmin
from app.models_and_views.serializer import query_serializer,comments_serializer, user_serializer,replace_with_ids,technology_serializer
from utils.pagination import get_paginated_list
from utils.smtp_mail import send_mail_to_reset_password

class Technologies(Resource):
    @authentication
    def post(self):
        data = request.get_json() or {}
        if not data:
            app.logger.info("No input(s)")
            return jsonify(status=400, message="No input(s)")
        user_id = data.get('user_id')
        technologies = data.get('technologies')
        if not (user_id and technologies):
            app.logger.info("User_id and technologies are required")
            return jsonify(status=404, message="User_id and technologies are required")
        check_user = User.query.filter_by(id=user_id).first()
        if not check_user:
            app.logger.info("User not found")
            return jsonify(status=400, message="User not found")
        if not (check_user.roles == 2 or check_user.roles == 3):
            app.logger.info("User not allowed to add technologies")
            return jsonify(status=404, message="User not allowed to add technologies")
        for itr in technologies:
            check_tech_exist = Technologies.query.filter_by(name=itr).first()
            if check_tech_exist:
                app.logger.info(f"{itr} technology already exists")
                return jsonify(status=400, message=f"{itr} technology already exists")
        today = datetime.now()
        date_time_obj = today.strftime('%Y/%m/%d %H:%M:%S')
        for itr in technologies:
            tech = Technologies(itr, date_time_obj, date_time_obj)
            db.session.add(tech)
            db.session.commit()
        return jsonify(status=200, message="added successfully")

    @authentication
    def delete(self):
        data = request.get_json() or {}
        if not data:
            app.logger.info("No input(s)")
            return jsonify(status=400, message="No input(s)")
        tech_id = data.get('tech_id')
        user_id = data.get('user_id')
        tech_check = db.session.query(Technologies).filter_by(id=tech_id).first()
        user_check = db.session.query(User).filter_by(id=user_id).first()

        if not (tech_id and user_id):
            app.logger.info("Query id, user_id required to delete")
            return jsonify(status=404, message="Query id, user_id required to delete")
        if not user_check:
            app.logger.info("User not found")
            return jsonify(status=400, message="User not found")
        if tech_check:
            if (user_check.roles != 1):
                db.session.delete(tech_check)
                db.session.commit()
                app.logger.info("Query deleted successfully")
                return jsonify(status=200, message="Query deleted successfully")
            app.logger.info("User not allowed to delete")
            return jsonify(status=404, message="User not allowed to delete")

        app.logger.info("Technology not found")
        return jsonify(status=400, message="Technology not found")
