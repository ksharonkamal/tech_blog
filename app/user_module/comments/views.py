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
from app.models_and_views.pagination import get_paginated_list
from utils.smtp_mail import send_mail_to_reset_password


class CommentClass(Resource):
    @authentication
    def post(self):
        data = request.get_json() or {}
        if not data:
            app.logger.info("No input(s)")
            return jsonify(status=400, message="No input(s)")
        query_id =data.get('query_id')
        user_id =data.get('user_id')
        queries_check =db.session.query(Queries).filter_by(id=query_id).first()
        # queries_check=Queries.objects.filter(id=query_id).first()
        user_check =db.session.query(User).filter_by(id=user_id).first()
        # user_check=User.objects.filter(id=user_id).first()
        if not (queries_check and user_check):
            app.logger.info("Query_id or user_id not found or not entered")
            return jsonify(status=404, message="Query_id or user_id not found or not entered")
        comment =data.get('comment')
        if not (query_id and user_id and comment):
            app.logger.info("query_id,user_id and comment are required")
            return jsonify(status=400 ,message="query_id,user_id and comment are required")
        today = datetime.now()
        date_time_obj = today.strftime('%Y/%m/%d %H:%M:%S')
        comm =Comments(user_id ,query_id ,comment ,date_time_obj ,date_time_obj)
        db.session.add(comm)
        db.session.commit()
        app.logger.info("comment inserterd succesfully")
        return jsonify(status=200 ,message="comment inserterd succesfully")

    @authentication
    def put(self):
        data =request.get_json() or {}
        if not data:
            app.logger.info("No input(s)")
            return jsonify(status=400, message="No input(s)")
        try:
            query_id =data.get('query_id')
            user_id =data.get('user_id')
            comment_id =data.get('comment_id')
            edit_comment_by_id =db.session.query(Comments).filter_by(id=comment_id).first()
            check_user =db.session.query(User).filter_by(id=user_id).first()
            check_queries_auth =db.session.query(Queries).filter_by(u_id=user_id).first()
        except:
            app.logger.info("comment/user/query not found")
            return jsonify("comment/user/query not found")
        edited_comment =data.get('edited_comment')
        if not (query_id and user_id and edited_comment and comment_id):
            app.logger.info("query_id , user_id , edited_comment and comment_id are required fields")
            return jsonify(status=400 ,message="query_id , user_id , edited_comment and comment_id are required fields")
        if not (check_queries_auth or check_user != 1):
            app.logger.info("cant edit comment")
            return jsonify(status=404 ,message="cant edit comment")
        if not edit_comment_by_id:
            app.logger.info("Comment not found")
            return jsonify(status=400 ,message="Comment not found")
        if not ((edit_comment_by_id.u_id == user_id) or check_user.roles == 2 or check_user.roles == 3):
            app.logger.info("User not allowed to edit")
            return jsonify(status=404 ,message="User not allowed to edit")
        edit_comment_by_id.msg =edited_comment
        db.session.commit()
        app.logger.info("Comment edited")
        return jsonify(status=200 ,message="Comment edited"
                       ,data={"query_id" :query_id ,"comment_id" :comment_id ,"edited_comment" :edited_comment})

    @authentication
    def delete(self):
        data =request.get_json() or {}
        if not data:
            app.logger.info("No input(s)")
            return jsonify(status=400, message="No input(s)")

        query_id =data.get('query_id')
        user_id =data.get('user_id')
        comment_id =data.get('comment_id')
        if not (query_id and user_id and comment_id):
            app.logger.info("Query_id , user_id and comment_id are required")
            return jsonify(status=200 ,message="Query_id , user_id and comment_id are required")
        query_check =db.session.query(Queries).filter_by(id=query_id).first()
        user_check =db.session.query(User).filter_by(id=user_id).first()
        if not user_check:
            app.logger.info("User not found")
            return jsonify(status=400 ,message="User not found")

        if not query_check:
            app.logger.info("Query not found")
            return jsonify(status=400 ,message="Query not found")
        comment_check =db.session.query(Comments).filter_by(id=comment_id).first()
        if not comment_check:
            app.logger.info("Comment not found")
            return jsonify(status=400 ,message="Comment not found")
        if not ((comment_check.u_id == user_id) or user_check.roles != 1):
            app.logger.info("User not allowed to delete")
            return jsonify(status=404 ,message="User not allowed to delete")
        db.session.delete(comment_check)
        db.session.commit()
        app.logger.info("Comment deleted successfully")
        return jsonify(status=200, message="Comment deleted successfully")

    def get(self):  # send all the comments based on comment_id or u_id or q_id or send all

        order_by_comment_obj = db.session.query(Comments).order_by(Comments.updated_at)
        if not order_by_comment_obj:
            app.logger.info("No Comments in DB")
            return jsonify(status=404, message="No comments in DB")

        c_list =[]
        for itr in order_by_comment_obj:
            dt = comments_serializer(itr)
            c_list.append(dt)

        app.logger.info("Return comments data")
        return jsonify(status=200, data=get_paginated_list(c_list, '/comment', start=request.args.get('start', 1),
                                                           limit=request.args.get('limit', 3)), message="Returning comments data")


class GetCommentByQueryId(Resource):
    def get(self,query_id):
        comment_obj = Comments.query.filter_by(q_id=query_id).all()
        if not comment_obj:
            app.logger.info("No Comments found")
            return jsonify(status=404, message="No comments found")
        comment_list=[]
        query_id_str=str(query_id)
        page = '/getcomments/query/'+query_id_str
        for itr in comment_obj:
            dt = comments_serializer(itr)
            comment_list.append(dt)
        app.logger.info("Return comments data")
        return jsonify(status=200, data=get_paginated_list(comment_list, page, start=request.args.get('start', 1),
                                          limit=request.args.get('limit', 3)), message="Returning queries data")


class GetCommentsByUserId(Resource):
    def get(self,user_id): #send all the comments based on user_id
        try:
            c_list = []
            comments_obj = db.session.query(Comments).filter_by(u_id=user_id).all()

            if not comments_obj:
                app.logger.info("No Comments in DB")
                return jsonify(status=404, message="No comments in DB")

            for itr in comments_obj:
                if itr.u_id == user_id:
                    dt = comments_serializer(itr)
                    c_list.append(dt)

            # if not c_list:
            #     app.logger.info("No comments in DB")
            #     return jsonify(status=404, message="No comments found")
            user_id_str=str(user_id)
            page = '/getcomments/user/'+user_id_str

            app.logger.info("Return comments data")
            return jsonify(status=200, data=get_paginated_list(c_list, page, start=request.args.get('start', 1),
                                          limit=request.args.get('limit', 3)), message="Returning queries data")

        except:
            return jsonify(status=400, message="No inputs found")
