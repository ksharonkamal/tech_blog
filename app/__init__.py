import logging
from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from flask_restplus import Api
from flask_cors import CORS
from flask_migrate import Migrate
app = Flask(__name__)
CORS(app)
cors = CORS(app, resources={r"": {"origins": ""}, })
# app.secret_key="IIOOOOOWREE"
app.config['SECRET_KEY'] = 'rmijlkqqqawtre@1((11'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Root@localhost/tech_support_database'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
db = SQLAlchemy(app)
migrate=Migrate(app,db)
api = Api(app)

from app.models_and_views.views import GetQueryByTechnology, GetQueryByUserId, Login, QueriesClass,\
Register,Logout,UpdatePassword,ForgotPassword,AddTechnologies,\
CommentClass,Queries_class,UserProfile, UserStatus,\
GetProfile,GetCommentByQueryId,GetCommentsByUserId,GetQueryByTechnology,Likes, DisLikes, FilterRecord


from app.admin_module.users.views import GetAllUsers, UserStatus, UserDelete
from app.admin_module.queries.views import GetQueryByUserId, QueriesClass
from app.admin_module.comments.views import GetCommentsByUserId, CommentClass
from app.admin_module.dashboard.views import Dashboard
from app.admin_module.technologies.views import Technologies


api.add_resource(Login, "/login")
api.add_resource(Register,"/register")
api.add_resource(Logout,"/logout")
api.add_resource(UpdatePassword,"/changepassword")
api.add_resource(ForgotPassword,"/forgotpassword")
api.add_resource(AddTechnologies,"/technologies")
api.add_resource(QueriesClass,"/query")
api.add_resource(CommentClass,"/comment")
api.add_resource(Queries_class,"/filter")
api.add_resource(UserProfile,"/profile")
api.add_resource(UserStatus,"/userstatuschange")
api.add_resource(GetProfile,"/getprofile/<int:user_id>")
api.add_resource(GetCommentByQueryId,"/getcomments/query/<int:query_id>")
api.add_resource(GetCommentsByUserId,"/getcomments/user/<int:user_id>")
api.add_resource(GetQueryByUserId,"/getqueries/user/<int:user_id>")
api.add_resource(GetQueryByTechnology,"/getqueries/technology/<string:technology>")
api.add_resource(GetQueryByUserId,"/getqueries/user/<int:user_id>")
api.add_resource(Likes,"/like")
api.add_resource(DisLikes,"/dislike")


api.add_resource(Dashboard,"/admin/toptenusers/<int:users_limit>")
api.add_resource(GetAllUsers,"/admin/getallusers")
api.add_resource(UserStatus, "/admin/userstatus")
api.add_resource(UserDelete, "/admin/userdelete")

api.add_resource(GetQueryByUserId, "/admin/getqueries/user/<int:user_id>")
api.add_resource(QueriesClass, "/admin/query")

api.add_resource(GetCommentsByUserId, "/admin/getcomments/user/<int:user_id>")
api.add_resource(CommentClass, "/admin/comment")

api.add_resource(Technologies, "/admin/technologies")

api.add_resource(FilterRecord, "/admin/filterrecords")
