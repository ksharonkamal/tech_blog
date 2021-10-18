from app.models_and_views.models import LikesDislikes, Comments
from flask import jsonify
from sqlalchemy import and_
from app import app,db


def update_like_dislike_count(self):  # insert the like and dislike count
    likes_dislikes_obj = LikesDislikes.query.filter().all()

    if not likes_dislikes_obj:
        app.logger.info("No comment are liked or disliked ")
        return jsonify(status=404, message="No comment are liked or disliked ")

    for itr in likes_dislikes_obj:
        cmt_like_count = LikesDislikes.query.filter(and_(LikesDislikes.c_id == itr.c_id),
                                                    (LikesDislikes.like_status == 1)).count()
        cmt_dislike_count = LikesDislikes.query.filter(and_(LikesDislikes.c_id == itr.c_id),
                                                       (LikesDislikes.dislike_status == 1)).count()

        comment_obj = Comments.query.filter_by(id=itr.c_id).first()
        comment_obj.like_count = cmt_like_count
        comment_obj.dislike_count = cmt_dislike_count
        db.session.commit()

    app.logger.info("Return comments data")
    return jsonify(status=200, message="like and dislike count updated")
