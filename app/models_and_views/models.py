from enum import unique
from flask_restplus.resource import Resource
from app import db
from datetime import datetime


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    email = db.Column(db.String(120), unique=True)
    mobile = db.Column(db.String(300), unique=True)
    technology = db.Column(db.String(200))
    password = db.Column(db.String(200))
    roles = db.Column(db.Integer, db.ForeignKey('roles.id'), default=1)
    status=db.Column(db.Boolean,default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    queries = db.relationship('Queries', backref='user_queries')
    comments = db.relationship('Comments', backref='user_comments')

    def __init__(self, name, email, mobile, technology, password, created_at, updated_at):
        self.name = name
        self.email = email
        self.mobile = mobile
        self.technology = technology
        self.password = password
        self.created_at = created_at
        self.updated_at = updated_at


class Technologies(db.Model):
    __tablename__ = "technologies"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True)
    status = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now())
    updated_at = db.Column(db.DateTime, default=datetime.now(), onupdate=datetime.now())
    queries = db.relationship('Queries', backref='queries_backref')

    def __init__(self, name, created_at, updated_at):
        self.name = name
        self.created_at = created_at
        self.updated_at = updated_at


class Queries(db.Model):
    __tablename__ = "queries"
    id = db.Column(db.Integer, primary_key=True)
    u_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    title = db.Column(db.String(300), unique=True)
    description = db.Column(db.Text)
    t_id = db.Column(db.Integer, db.ForeignKey('technologies.id'))
    file_path = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now())
    updated_at = db.Column(db.DateTime, default=datetime.now(), onupdate=datetime.now())
    status = db.Column(db.Boolean, default=True)
    comments = db.relationship('Comments', backref='comments_on_queries')

    def __init__(self, u_id, title, description, t_id, created_at, updated_at):
        self.u_id = u_id
        self.title = title
        self.description = description
        self.t_id = t_id
        self.created_at = created_at
        self.updated_at = updated_at


class Comments(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    u_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    q_id = db.Column(db.Integer, db.ForeignKey('queries.id'))
    msg = db.Column(db.Text)
    like_count = db.Column(db.Integer, default=0)
    dislike_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now())
    updated_at = db.Column(db.DateTime, default=datetime.now(), onupdate=datetime.now())
    status = db.Column(db.Boolean, default=True)

    def __init__(self, u_id, q_id, msg, created_at, updated_at):
        self.u_id = u_id
        self.q_id = q_id
        self.msg = msg
        self.created_at = created_at
        self.updated_at = updated_at


class Roles(db.Model):
    __tablename__ = "roles"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))


# db.create_all()

class LikesDislikes(db.Model):
    __tablename__ = "likesdislikes"
    id = db.Column(db.Integer, primary_key=True)
    u_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    c_id = db.Column(db.Integer, db.ForeignKey('comments.id'))
    like_status = db.Column(db.Boolean, default=False)
    dislike_status=db.Column(db.Boolean,default=False)
    created_at = db.Column(db.DateTime, default=datetime.now())
    updated_at = db.Column(db.DateTime, default=datetime.now(), onupdate=datetime.now())

    def __init__(self, u_id, c_id, like_status,dislike_status, created_at, updated_at):
        self.u_id = u_id
        self.c_id = c_id
        self.like_status = like_status
        self.dislike_status=dislike_status
        self.created_at = created_at
        self.updated_at = updated_at

# from enum import unique
# from app import db
# from datetime import datetime

# class User(db.Model):
#     __tablename__ = "users"
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(80), unique=True)
#     email = db.Column(db.String(120), unique=True)
#     mobile = db.Column(db.String(300), unique=True)
#     technology = db.Column(db.String(200))
#     password = db.Column(db.String(200))
#     created_at = db.Column(db.DateTime, default=datetime.now)
#     updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

#     def __init__(self, name, email, mobile, technology,password,created_at,updated_at):
#         self.name = name
#         self.email = email
#         self.mobile = mobile
#         self.technology = technology
#         self.password=password
#         self.created_at=created_at
#         self.updated_at=updated_at

# class technologies(db.Model):
#     __tablename__ = "technologies"
#     id=db.Column(db.Integer,primary_key=True )
#     name=db.Column(db.String(80),unique=True)
#     status=db.Column(db.Boolean)
#     created_at=db.Column(db.DateTime,default=datetime.now())
#     updated_at=db.Column(db.DateTime,default=datetime.now(),onupdate=datetime.now())

#     def __init__(self,name,status,created_at,updated_at):
#         self.name=name
#         self.status=status
#         self.created_at=created_at
#         self.updated_at=updated_at

# class Queries(db.Model):
#     __tablename__ = "queries"
#     id=db.Column(db.Integer,primary_key=True)
#     u_id=db.Column(db.Integer,unique=True)
#     title=db.Column(db.Text)
#     description=db.Column(db.Text)
#     images_links=db.Column(db.Text)
#     t_id=db.Column(db.Integer)
#     created_at=db.Column(db.DateTime,default=datetime.now())
#     updated_at=db.Column(db.DateTime,default=datetime.now(),onupdate=datetime.now())

#     def __init__(self,u_id,title,description,images_links,t_id,created_at,updated_at):
#         self.id=id
#         self.u_id=u_id
#         self.title=title
#         self.description=description
#         self.images_links=images_links
#         self.t_id=t_id
#         self.created_at=created_at
#         self.updated_at=updated_at

db.create_all()