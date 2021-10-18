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
from utils.update_like_dislike_count import update_like_dislike_count


class Dashboard(Resource):
    def get(self, users_limit):
        update_like_dislike_count(self)
        top_ten_list = []
        top_ten_users_list = []
        count = 0

        comment_obj_list = Comments.query.filter(Comments.like_count>=Comments.dislike_count).\
            order_by(Comments.like_count.desc()).all()
        print(comment_obj_list)

        if not comment_obj_list:
            app.logger.info("No comments in db")
            return jsonify(status=400, message="No comments in db")

        for itr in comment_obj_list:
            if itr.like_count and count<users_limit:
                print("cmt_id=", itr.id, "Like count = ", itr.like_count, "dislike count =", itr.dislike_count)
                user_obj = User.query.filter_by(id=itr.u_id).first()
                if not user_obj:
                    app.logger.info("No user in db")
                    return jsonify(status=400, message="No user in db")
                top_ten_users_list.append(user_obj)
                count=count+1

        if not top_ten_users_list:
            app.logger.info("No top users")
            return jsonify(status=400, message="No top users")

        for itr in top_ten_users_list:
            dt = user_serializer(itr)
            top_ten_list.append(dt)
        app.logger.info("Return top 10 user data")

        page = "/admin/toptenusers/" + f'{users_limit}'

        return jsonify(status=200, data=get_paginated_list(top_ten_list,page, start=request.args.get('start', 1),
                                          limit=request.args.get('limit', 3)), message="Returning top 10 use data")
        # return jsonify(status=200, data=top_ten_list, message="Returning top 10 use data")
