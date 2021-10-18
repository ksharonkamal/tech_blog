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
from app.models_and_views.pagination import get_paginated_list
from utils.smtp_mail import send_mail_to_reset_password
from flask import jsonify, request


class QueriesClass(Resource):
    @authentication
    def post(self):
        data = request.get_json()
        if not data:
            app.logger.info("No input(s)")
            return jsonify(status=400, message="No input(s)")
        try:
            user_id = data.get('user_id')
            user_check = db.session.query(User).filter_by(id=user_id).first()
            print(user_check)
            tech = data.get('technology')
            tech_check = db.session.query(Technologies).filter_by(name=tech).first()
        except:
            app.logger.info("(User/tech) not found")
            return jsonify(status=400, message="(User/tech) not found")
        title = data.get('title')
        description = data.get('description')

        if not (title and description and tech and user_id):
            app.logger.info("title, description, user_id and technology are required")
            return jsonify(status=200, message="title, description, user_id and technology are required")
        if not tech_check:
            app.logger.info("technology not found")
            return jsonify(status=400, message="technology not found")

        query_insertion = db.session.query(Queries).filter(or_(Queries.title == title,
                                                               Queries.description == description)).first()

        if query_insertion:
            if query_insertion.title == title:
                app.logger.info("Data already exist")
                return jsonify(status=200, message="Data already exist")

        today = datetime.now()
        date_time_obj = today.strftime('%Y/%m/%d %H:%M:%S')
        try:
            question = Queries(user_id, title, description, tech_check.id, date_time_obj, date_time_obj)
            db.session.add(question)
            db.session.commit()
        except:
            app.logger.info("user not found")
            return jsonify(status=400, message="user not found")
        app.logger.info("Query inserted successfully")
        response = query_serializer(question)
        return jsonify(status=200, data=response, message="Query inserted successfully")

    @authentication
    def put(self):
        data = request.get_json()
        if not data:
            app.logger.info("No input(s)")
            return jsonify(status=400, message="No input(s)")
        try:
            query_id = data.get('query_id')
            user_id = data.get('user_id')
            user_check = db.session.query(User).filter_by(id=user_id).first()
            tech = data.get('technology')
            tech_check = db.session.query(Technologies).filter_by(name=tech).first()
            query_check = db.session.query(Queries).filter_by(id=query_id).first()
        except:
            app.logger.info("(query_id/user_id/tech_list) not found")
            return jsonify(status=400, message="(query_id/user_id/tech_list) not found")
        title = data.get('title')
        description = data.get('description')

        if not (query_id and user_id and title and description and tech):
            app.logger.info("Query id , User id , title , description, technology are required fields")
            return jsonify(status=404,
                           message="Query id , User id , title , description, technology are required fields")
        if not (user_check and tech_check):
            app.logger.info("User or technology not found")
            return jsonify(status=400, message="User or technology not found")
        if query_check:
            if ((query_check.u_id == user_id) or (user_check.roles != 1)):
                query_check.title = title
                query_check.description = description
                query_check.t_id = tech_check.id
                today = datetime.now()
                date_time_obj = today.strftime('%Y/%m/%d %H:%M:%S')
                query_check.updated_at = date_time_obj
                db.session.commit()
                response = {"query_id": query_check.id, "title": query_check.title,
                            "description": query_check.description, "technology": tech}
                app.logger.info("Query changed successfully")
                return jsonify(status=200, data=response, message="Query changed successfully")
            app.logger.info("User not allowed to edit")
            return jsonify(status=404, message="User not allowed to edit")
        app.logger.info("Query didn't found")
        return jsonify(status=404, message="Query didn't found")

    @authentication
    def delete(self):
        data = request.get_json() or {}
        if not data:
            app.logger.info("No input(s)")
            return jsonify(status=400, message="No input(s)")
        try:
            query_id = data.get('query_id')
            user_id = data.get('user_id')
            query_check = db.session.query(Queries).filter_by(id=query_id).first()
            user_check = db.session.query(User).filter_by(id=user_id).first()
        except:
            app.logger.info("user_id/query_id not found")
            return jsonify(status=400, message="user_id/query_id not found")

        if not (query_id and user_id):
            app.logger.info("Query id, user_id required to delete")
            return jsonify(status=404, message="Query id, user_id required to delete")
        if query_check:
            if ((query_check.u_id == user_id) or (user_check.roles != 1)):
                delete_comment = db.session.query(Comments).filter_by(q_id=query_id).all()
                if delete_comment:
                    for itr in delete_comment:
                        db.session.delete(itr)
                        db.session.commit()
                else:
                    app.logger.info("No comments for this query, deleting this query ")
                db.session.delete(query_check)
                db.session.commit()
                app.logger.info("Query deleted successfully")
                return jsonify(status=200, message="Query deleted successfully")
            app.logger.info("User not allowed to delete")
            return jsonify(status=404, message="User not allowed to delete")

        app.logger.info("Query not found")
        return jsonify(status=400, message="Query not found")

    def get(self):  # send all the comments based on comment_id or u_id or q_id or send all
        order_by_query_obj = db.session.query(Queries).order_by(Queries.updated_at)
        if not order_by_query_obj:
            app.logger.info("No Queries in DB")
            return jsonify(status=404, message="No Queries in DB")

        c_list = []
        for itr in order_by_query_obj:
            dt = query_serializer(itr)
            c_list.append(dt)

        app.logger.info("Return queries data")
        return jsonify(status=200, data=get_paginated_list(c_list, '/query', start=request.args.get('start', 1),
                                                           limit=request.args.get('limit', 3)),
                       message="Returning queries data")


class GetQueryByUserId(Resource):
    def get(self,user_id):
        queries_obj = db.session.query(Queries).filter_by(u_id=user_id).all()
        if not queries_obj:
            app.logger.info("No queries found")
            return jsonify(status=404, message="No queries found")
        queries_list=[]
        for itr in queries_obj:
            dt = query_serializer(itr)
            queries_list.append(dt)
        user_id_str=str(user_id)
        page = '/getqueries/user/'+user_id_str
        app.logger.info("Returning queries data")
        return jsonify(status=200, data=get_paginated_list(queries_list, page, start=request.args.get('start', 1),
                                          limit=request.args.get('limit', 3)), message="Returning queries data")


class GetQueryByTitle(Resource):
    def get(self,title):
        queries_obj = db.session.query(Queries).filter_by(title=title).first()
        if not queries_obj:
            app.logger.info("No queries found")
            return jsonify(status=404, message="No queries found")
        queries_list=[]
        page = '/getqueries/user/'+title
        app.logger.info("Returning query data")
        return jsonify(status=200, data=get_paginated_list(query_serializer(queries_obj), page, start=request.args.get('start', 1),
                                          limit=request.args.get('limit', 3)), message="Returning queries data")


class GetQueryByTechnology(Resource):
    def get(self,technology):
        tech_obj=db.session.query(Technologies).filter_by(name=technology).first()
        if not tech_obj:
            app.logger.info("technology not found")
            return jsonify(status=404, message="technology not found")

        queries_obj = db.session.query(Queries).filter_by(t_id=tech_obj.id).all()
        if not queries_obj:
            app.logger.info("No queries found")
            return jsonify(status=404, message="No queries found")
        queries_list=[]
        for itr in queries_obj:
            dt = query_serializer(itr)
            queries_list.append(dt)
        page = '/getqueries/technology/'+technology
        app.logger.info("Returning queries data")
        return jsonify(status=200, data=get_paginated_list(queries_list, page, start=request.args.get('start', 1),
                                          limit=request.args.get('limit', 3)), message="Returning queries data")
