from flask_restplus import Resource
from flask import request
from app.models_and_views.models import Comments
from flask import jsonify
from app import app,db
from app.models_and_views.models import User,LikesDislikes
from datetime import datetime
from sqlalchemy import and_
from utils.update_like_dislike_count import update_like_dislike_count


class Likes(Resource):
    def post(self):
        data=request.get_json() or {}
        user_id=data.get('user_id')
        comment_id=data.get('comment_id')
        if not (user_id and comment_id):
             app.logger.info("user_id and comment_id are required")
             return jsonify(status=400,message="user_id and comment_id are required")
        user_obj=User.query.filter_by(id=user_id).first()
        comment_obj=Comments.query.filter_by(id=comment_id).first()
        if not user_obj:
            app.logger.info("user not found")
            return jsonify(status=400, message="user not found")
        if not comment_obj:
            app.logger.info("comment not found")
            return jsonify(status=400, message="comment not found")
        likes_dislikes_obj=LikesDislikes.query.filter(and_(LikesDislikes.u_id==user_id,
                                                           LikesDislikes.c_id==comment_id)).first()
        if  likes_dislikes_obj:
            if likes_dislikes_obj.dislike_status:
                likes_dislikes_obj.like_status = True
                likes_dislikes_obj.dislike_status = False
                db.session.commit()
                app.logger.info("liked")
                return jsonify(status=200, message="liked")
            else:
                db.session.delete(likes_dislikes_obj)
                db.session.commit()
                app.logger.info("like or dislike removed")
                return jsonify(status=200, message="like or dislike removed")
            likes_dislikes_obj.like_status=True
            likes_dislikes_obj.dislike_status=False
            db.session.commit()
            app.logger.info("liked")
            return jsonify(status=200, message="liked")

        today = datetime.now()
        date_time_obj = today.strftime('%Y/%m/%d %H:%M:%S')
        like = True
        dislike = False
        like_dislike_record = LikesDislikes(user_id, comment_id, like, dislike, date_time_obj, date_time_obj)
        db.session.add(like_dislike_record)
        db.session.commit()
        update_like_dislike_count(self)
        app.logger.info("Liked")
        return jsonify(status=200, message="Liked")


class DisLikes(Resource):
    def post(self):
        data=request.get_json() or {}
        user_id=data.get('user_id')
        comment_id=data.get('comment_id')
        if not (user_id and comment_id):
             app.logger.info("user_id and comment_id are required")
             return jsonify(status=400,message="user_id and comment_id are required")
        user_obj=User.query.filter_by(id=user_id).first()
        comment_obj=Comments.query.filter_by(id=comment_id).first()
        if not user_obj:
            app.logger.info("user not found")
            return jsonify(status=400, message="user not found")
        if not comment_obj:
            app.logger.info("comment not found")
            return jsonify(status=400, message="comment not found")
        likes_dislikes_obj=LikesDislikes.query.filter(and_(LikesDislikes.u_id==user_id,
                                                           LikesDislikes.c_id==comment_id)).first()
        if  likes_dislikes_obj:
            if likes_dislikes_obj.like_status:
                likes_dislikes_obj.like_status = False
                likes_dislikes_obj.dislike_status = True
                db.session.commit()
                app.logger.info("disliked")
                return jsonify(status=200, message="disliked")
            else:
                db.session.delete(likes_dislikes_obj)
                db.session.commit()
                app.logger.info("like or dislike removed")
                return jsonify(status=200, message="like or dislike removed")
            # if (likes_dislikes_obj.like_status or likes_dislikes_obj.dislike_status):
                # LikesDislikes.query.filter(c_id=comment_id).update(like_status=False,dislike_status=False)
            likes_dislikes_obj.like_status=False
            likes_dislikes_obj.dislike_status=True
            db.session.commit()
            app.logger.info("liked or disliked")
            return jsonify(status=200, message="liked or disliked")

        today = datetime.now()
        date_time_obj = today.strftime('%Y/%m/%d %H:%M:%S')
        like = False
        dislike = True
        like_dislike_record = LikesDislikes(user_id, comment_id, like, dislike, date_time_obj, date_time_obj)
        db.session.add(like_dislike_record)
        db.session.commit()
        update_like_dislike_count(self)
        app.logger.info("DisLiked")
        return jsonify(status=200, message="DisLiked")
