from flask import jsonify, request
from sqlalchemy.future import select
from sqlalchemy.sql import or_
from flask_restplus import Resource
from datetime import datetime
from sqlalchemy.orm import query
from sqlalchemy.sql.expression import delete
from sqlalchemy.sql.functions import user
from werkzeug.security import generate_password_hash, check_password_hash
from .models import User, Technologies, Queries, Comments, LikesDislikes
from app import app, db
from sqlalchemy import or_,and_,desc
import re,ast
from app.authentication import encode_auth_token,authentication
#is_admin_or_superadmin
from .serializer import query_serializer,comments_serializer, user_serializer,replace_with_ids,technology_serializer
from .pagination import get_paginated_list
from utils.smtp_mail import send_mail_to_reset_password
from utils.update_like_dislike_count import update_like_dislike_count


# from utils import smtp_mail
#over and admin
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

#over
class Logout(Resource):
    def post(self):
        app.logger.info("Logged out successfully")
        return jsonify(status=200, message="Logged out successfully")

    def get(self):
        app.logger.info("Logged out successfully")
        return jsonify(status=200, message="Logged out successfully")

#over
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
                    ids_list=f"{replace_with_ids(list_of_tech)}"

                    print(ids_list)

                    # technology = ast.literal_eval(technology)
                    today = datetime.now()
                    date_time_obj = today.strftime('%Y/%m/%d %H:%M:%S')
                    print(date_time_obj)
                    password=generate_password_hash(password, method='sha256')
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

#over
class UpdatePassword(Resource):
    @authentication
    def put(self):
        data=request.get_json() or {}
        email=data.get("email")
        mobile=data.get("mobile")
        old_password=data.get("old_password")
        new_password=data.get("new_password")
        confirm_new_password=data.get("confirm_new_password")

        if not ((email or mobile) and (old_password and new_password and confirm_new_password)):
            app.logger.info(f'email (or) mobile , old_password, new_password and confirm_new_password required')
            return jsonify(status=400, message="email (or) mobile , old_password, new_password and confirm_new_password required")
        try:
         user = db.session.query(User).filter(or_(User.email == email, User.mobile == mobile)).first()
         if user:
            if check_password_hash(user.password, data.get('old_password')):
                if new_password == confirm_new_password:
                    if new_password == old_password:
                        app.logger.info("New password and old password should not be same")
                        return jsonify(status=400, message="New password and old password should not be same")
                    if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!#%*?&]{6,20}$', new_password):
                        app.logger.info("Password should contain min 8 characters, a special character, Uppercase, lowercase and a number")
                        return jsonify(status=400,message='Password should contain min 8 characters, a special character, Uppercase, lowercase and a number')
                    user.password=generate_password_hash(new_password, method='sha256')
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
             return jsonify(status=404,message="Unknown database")

#over and admin
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

#overAdmin
class AddTechnologies(Resource):
    # @authentication
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
    
#over and admin
class QueriesClass(Resource):
    @authentication
    def post(self):
        data = request.get_json()
        if not data:
            app.logger.info("No input(s)")
            return jsonify(status=400, message="No input(s)")
        try:
            user_id = data.get('user_id')
            user_check=db.session.query(User).filter_by(id=user_id).first()
            print(user_check)
            tech = data.get('technology')
            tech_check=db.session.query(Technologies).filter_by(name=tech).first()
        except:
            app.logger.info("(User/tech) not found")
            return jsonify(status=400,message="(User/tech) not found")
        title = data.get('title')
        description = data.get('description')

        if not (title and description and tech and user_id):
            app.logger.info("title, description, user_id and technology are required")
            return jsonify(status=200, message="title, description, user_id and technology are required")
        if not tech_check:
            app.logger.info("technology not found")
            return jsonify(status=400,message="technology not found")

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
            return jsonify(status=400,message="user not found")
        app.logger.info("Query inserted successfully")
        response = query_serializer(question)
        return jsonify(status=200, data=response, message="Query inserted successfully")

    @authentication
    def put(self):
        data=request.get_json()
        if not data:
            app.logger.info("No input(s)")
            return jsonify(status=400, message="No input(s)")
        try:
            query_id=data.get('query_id')
            user_id=data.get('user_id')
            user_check=db.session.query(User).filter_by(id=user_id).first()
            tech = data.get('technology')
            tech_check=db.session.query(Technologies).filter_by(name=tech).first()
            query_check=db.session.query(Queries).filter_by(id=query_id).first()
        except:
            app.logger.info("(query_id/user_id/tech_list) not found")
            return jsonify(status=400,message="(query_id/user_id/tech_list) not found")
        title = data.get('title')
        description = data.get('description')
        

        if not (query_id and user_id and title and description and tech):
            app.logger.info("Query id , User id , title , description, technology are required fields")
            return jsonify(status=404, message="Query id , User id , title , description, technology are required fields")
        if not (user_check and tech_check):
            app.logger.info("User or technology not found")
            return jsonify(status=400,message="User or technology not found")
        if query_check:
            if  ((query_check.u_id == user_id) or (user_check.roles != 1)):
                query_check.title=title
                query_check.description=description
                query_check.t_id=tech_check.id
                today = datetime.now()
                date_time_obj = today.strftime('%Y/%m/%d %H:%M:%S')
                query_check.updated_at=date_time_obj
                db.session.commit()
                response={"query_id":query_check.id,"title":query_check.title,"description":query_check.description,"technology":tech}
                app.logger.info("Query changed successfully")
                return jsonify(status=200,data=response,message="Query changed successfully")
            app.logger.info("User not allowed to edit")
            return jsonify(status=404,message="User not allowed to edit")
        app.logger.info("Query didn't found")
        return jsonify(status=404,message="Query didn't found")
            
    
    @authentication
    def delete(self):
        data=request.get_json() or {}
        if not data:
            app.logger.info("No input(s)")
            return jsonify(status=400, message="No input(s)")
        try:
            query_id=data.get('query_id')
            user_id=data.get('user_id')
            query_check=db.session.query(Queries).filter_by(id=query_id).first()
            user_check=db.session.query(User).filter_by(id=user_id).first()
        except:
            app.logger.info("user_id/query_id not found")
            return jsonify(status=400,message="user_id/query_id not found")

        if not (query_id and user_id):
            app.logger.info("Query id, user_id required to delete")
            return jsonify(status=404,message="Query id, user_id required to delete")
        if query_check:
            if ((query_check.u_id == user_id) or (user_check.roles!=1)):
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
            return jsonify(status=404,message="User not allowed to delete")
            
        app.logger.info("Query not found")
        return jsonify(status=400,message="Query not found")

    def get(self): #send all the comments based on comment_id or u_id or q_id or send all
        
        order_by_query_obj = db.session.query(Queries).order_by(Queries.updated_at)
        if not order_by_query_obj:
                app.logger.info("No Queries in DB")
                return jsonify(status=404, message="No Queries in DB")

        c_list=[]   
        for itr in order_by_query_obj:
            dt = query_serializer(itr)
            c_list.append(dt)

        app.logger.info("Return queries data")
        return jsonify(status=200, data=get_paginated_list(c_list, '/query', start=request.args.get('start', 1),
                                          limit=request.args.get('limit', 3)), message="Returning queries data")

#over and admin
class CommentClass(Resource):
    @authentication
    def post(self):
        data = request.get_json() or {}
        if not data:
            app.logger.info("No input(s)")
            return jsonify(status=400, message="No input(s)")
        query_id=data.get('query_id')
        user_id=data.get('user_id')
        queries_check=db.session.query(Queries).filter_by(id=query_id).first()
        #queries_check=Queries.objects.filter(id=query_id).first()
        user_check=db.session.query(User).filter_by(id=user_id).first()
        #user_check=User.objects.filter(id=user_id).first()
        if not (queries_check and user_check):
            app.logger.info("Query_id or user_id not found or not entered")
            return jsonify(status=404, message="Query_id or user_id not found or not entered") 
        comment=data.get('comment')
        if not (query_id and user_id and comment ):
            app.logger.info("query_id,user_id and comment are required")
            return jsonify(status=400,message="query_id,user_id and comment are required")
        today = datetime.now()
        date_time_obj = today.strftime('%Y/%m/%d %H:%M:%S')
        comm=Comments(user_id,query_id,comment,date_time_obj,date_time_obj)
        db.session.add(comm)
        db.session.commit()
        app.logger.info("comment inserterd succesfully")
        return jsonify(status=200,message="comment inserterd succesfully")

    @authentication
    def put(self):
        data=request.get_json() or {}
        if not data:
            app.logger.info("No input(s)")
            return jsonify(status=400, message="No input(s)")
        try:
            query_id=data.get('query_id')
            user_id=data.get('user_id')
            comment_id=data.get('comment_id')
            edit_comment_by_id=db.session.query(Comments).filter_by(id=comment_id).first()
            check_user=db.session.query(User).filter_by(id=user_id).first()
            check_queries_auth=db.session.query(Queries).filter_by(u_id=user_id).first()
        except:
            app.logger.info("comment/user/query not found")
            return jsonify("comment/user/query not found")
        edited_comment=data.get('edited_comment')
        if not (query_id and user_id and edited_comment and comment_id):
            app.logger.info("query_id , user_id , edited_comment and comment_id are required fields")
            return jsonify(status=400,message="query_id , user_id , edited_comment and comment_id are required fields")
        if not (check_queries_auth or check_user != 1):
            app.logger.info("cant edit comment")
            return jsonify(status=404,message="cant edit comment")
        if not edit_comment_by_id:
            app.logger.info("Comment not found")
            return jsonify(status=400,message="Comment not found")
        if not ((edit_comment_by_id.u_id == user_id) or check_user.roles == 2 or check_user.roles == 3):
            app.logger.info("User not allowed to edit")
            return jsonify(status=404,message="User not allowed to edit")
        edit_comment_by_id.msg=edited_comment
        db.session.commit()
        app.logger.info("Comment edited")
        return jsonify(status=200,message="Comment edited",data={"query_id":query_id,"comment_id":comment_id,"edited_comment":edited_comment})
    
    @authentication
    def delete(self):
        data=request.get_json() or {}
        if not data:
            app.logger.info("No input(s)")
            return jsonify(status=400, message="No input(s)")
        
        query_id=data.get('query_id')
        user_id=data.get('user_id')
        comment_id=data.get('comment_id')
        if not (query_id and user_id and comment_id):
            app.logger.info("Query_id , user_id and comment_id are required")
            return jsonify(status=200,message="Query_id , user_id and comment_id are required")
        query_check=db.session.query(Queries).filter_by(id=query_id).first()
        user_check=db.session.query(User).filter_by(id=user_id).first()
        if not user_check:
            app.logger.info("User not found")
            return jsonify(status=400,message="User not found")

        if not query_check:
            app.logger.info("Query not found")
            return jsonify(status=400,message="Query not found")
        comment_check=db.session.query(Comments).filter_by(id=comment_id).first()
        if not comment_check:
            app.logger.info("Comment not found")
            return jsonify(status=400,message="Comment not found")
        if not ((comment_check.u_id == user_id) or user_check.roles != 1):
                app.logger.info("User not allowed to delete")
                return jsonify(status=404,message="User not allowed to delete")
        db.session.delete(comment_check)
        db.session.commit()
        app.logger.info("Comment deleted successfully")
        return jsonify(status=200, message="Comment deleted successfully")
    
    def get(self): #send all the comments based on comment_id or u_id or q_id or send all
        
        order_by_comment_obj = db.session.query(Comments).order_by(Comments.updated_at)
        if not order_by_comment_obj:
                app.logger.info("No Comments in DB")
                return jsonify(status=404, message="No comments in DB")

        c_list=[]   
        for itr in order_by_comment_obj:
            dt = comments_serializer(itr)
            c_list.append(dt)

        app.logger.info("Return comments data")
        return jsonify(status=200, data=get_paginated_list(c_list, '/comment', start=request.args.get('start', 1),
                                          limit=request.args.get('limit', 3)), message="Returning comments data")
    
            
class Queries_class(Resource):
   def get(self):
       try:
            t_list = []
            data = request.get_json() or {}

            for keys in data:
                if not keys in (''):
                    app.logger.info("No input found")
                    return jsonify(status=400,message="No input found")

            technology_obj = db.session.query(Technologies)
            order_by_technology_obj = technology_obj.order_by(Technologies.updated_at)

            if not technology_obj:
                app.logger.info("No Technologies in DB")
                return jsonify(status=404, message="No Technologies in DB")

            for itr in order_by_technology_obj:
                dt = technology_serializer(itr)
                t_list.append(dt)

            if not t_list:
                app.logger.info("No Technologies in DB")
                return jsonify(status=404, message="No Technologies in DB")

            app.logger.info("Return Technologies data")
            return jsonify(status=200, data=t_list, message="Returning Technologies data")
       except:
            app.logger.info("No input found")
            return jsonify(status=400,message="No input found")

#over
class UserProfile(Resource):
    def put(self):
        data = request.get_json() or {}
        try:
            user_id=data.get('user_id')
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
                user_update.technology= ids_list
                today = datetime.now()
                user_update.date_time_obj = today.strftime('%Y/%m/%d %H:%M:%S')
                db.session.commit()
                response = {"name": user_update.name, "technology": technology}
                app.logger.info(f'{user_update.name} Updated successfully')
                return jsonify(status=200, data=response, message="updated Successfully")

                        
        #    except:
        #         app.logger.info("database not established")
        #         return jsonify(status=404, message="database not established")

#admin
class UserStatus(Resource):
    @authentication
    def put(self):
        data=request.get_json() or {}
        if not data:
            app.logger.info("No input(s)")
            return jsonify(status=400, message="No input(s)")
        user_id=data.get('user_id')
        change_user_id=data.get('change_user_id')
        change_user_role=data.get('change_user_role')
        if not (change_user_id and user_id and change_user_role):
            app.logger.info("change_user_id and user id and change_user_role are required fields")
            return jsonify(status=404, message="change_user_id and user id and change_user_role are required fields")
        user_check=db.session.query(User).filter_by(id=user_id).first()
        if not user_check:
            app.logger.info("User not found")
            return jsonify(status=400,message="User not found")
        change_user_role=db.session.query(User).filter_by(id=change_user_id).first()
        if not change_user_role:
            app.logger.info("User you wanted to change role not found")
            return jsonify(status=400,message="User you wanted to change role not found")

        if  user_check.roles == 2:
            change_user_role.roles=2
            today = datetime.now()
            date_time_obj = today.strftime('%Y/%m/%d %H:%M:%S')
            change_user_role.updated_at=date_time_obj
            db.session.commit()
            app.logger.info(f"{change_user_role.name} role changed successfully")
            return jsonify(status=200,message=f"{change_user_role.name} role changed successfully")
        app.logger.info("User not allowed to perform this action")
        return jsonify(status=404,message="User not allowed to perform this action")

    
    @authentication
    def delete(self):
        data=request.get_json() or {}
        if not data:
            app.logger.info("No input(s)")
            return jsonify(status=400, message="No input(s)")
        user_id=data.get('user_id')
        delete_user=data.get('delete_user_id')
        if not (delete_user and user_id):
            app.logger.info("delete_user_id and User id are required fields")
            return jsonify(status=404, message="delete_user_id and User id are required fields")
        user_check=db.session.query(User).filter_by(id=user_id).first()
        if not user_check:
            app.logger.info("User not found")
            return jsonify(status=400,message="User not found")
        delete_user=db.session.query(User).filter_by(id=delete_user).first()
        if not delete_user:
            app.logger.info("User wanted to delete not found")
            return jsonify(status=400,message="User wanted to delete not found")

        if user_check.roles != 1:
            delete_user.status=0  # changed from roles to status
            today = datetime.now()
            date_time_obj = today.strftime('%Y/%m/%d %H:%M:%S')
            delete_user.updated_at=date_time_obj
            db.session.commit()
            app.logger.info(f"{delete_user} disabled successfully")
            return jsonify(status=200,message=f"{delete_user} disabled successfully")
        app.logger.info("User not allowed to perform this action")
        return jsonify(status=404,message="User not allowed to perform this action")
        
#over and admin
class GetProfile(Resource):
    def get(self,user_id):
        user_data=db.session.query(User).filter_by(id=user_id).first()
        if not user_data:
            app.logger.info("user not found")
            return jsonify(status=400, message="user not found")
        return jsonify(status=200,data=user_serializer(user_data),message="user data")

#over
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


class GetCommentsUserId(Resource):

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

            if not c_list:
                app.logger.info("No comments in DB")
                return jsonify(status=404, message="No comments found")
            user_id_str=str(user_id)
            page = '/getcomments/user/'+user_id_str

            app.logger.info("Return comments data")
            return jsonify(status=200, data=get_paginated_list(c_list, page, start=request.args.get('start', 1),
                                          limit=request.args.get('limit', 3)), message="Returning queries data")

        except:
            return jsonify(status=400, message="No inputs found")

#over and admin
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

#over and Admin
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

#over
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

#over
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
        app.logger.info("DisLiked")
        return jsonify(status=200, message="DisLiked")


class Dashboard(Resource):

    def get(self):
        update_like_dislike_count(self)
        top_ten_list = []
        top_ten_users_list = []
        count = 0

        comment_obj_list = Comments.query.filter(Comments.like_count>=Comments.dislike_count).\
            order_by(Comments.like_count.desc()).all()

        if not comment_obj_list:
            app.logger.info("No comments in db")
            return jsonify(status=400, message="No comments in db")

        for itr in comment_obj_list:
            if itr.like_count and count<10:
                # print("cmt_id=", itr.id, "Like count = ", itr.like_count, "dislike count =", itr.dislike_count)
                user_obj = User.query.filter_by(id=itr.u_id).first()
                if not user_obj:
                    app.logger.info("No user in db")
                    return jsonify(status=400, message="No user in db")
                top_ten_users_list.append(user_obj)
                count=count+1

        for itr in top_ten_users_list:
            dt = user_serializer(itr)
            top_ten_list.append(dt)
        app.logger.info("Return top 10 user data")
        return jsonify(status=200, data=get_paginated_list(top_ten_list, "/toptenusers", start=request.args.get('start', 1),
                                          limit=request.args.get('limit', 3)), message="Returning top 10 use data")


class FilterRecord(Resource):
    @authentication
    def post(self):
        data = request.get_json() or {}
        if not data:
            app.logger.info("No input(s)")
            return jsonify(status=400, message="No input(s)")
        from_date = data.get('from_date')
        to_date = data.get('to_date')
        users=data.get('users')
        queries=data.get('queries')
        technologies=data.get('technologies')
        if not (from_date and to_date): #and (users or queries or technologies)
            app.logger.info("from_date , to_date are required fields") #and user or queries or technologies
            return jsonify(status=400,message="from_date , to_date and user or queries or technologies are required fields")
        if users:
            table_name=User
        elif queries:
            table_name=Queries
        elif technologies:
            table_name=Technologies
        get_records_from_to=table_name.query.filter(and_(table_name.updated_at >= from_date,
                                                         table_name.updated_at <= to_date)).count()

        if not get_records_from_to:
            app.logger.info("No records found")
            return jsonify(status=200,message="No records found")
        records_list=[]
        for itr_record in get_records_from_to:
            if users:
                dt=user_serializer(itr_record)
            elif queries:
                dt=query_serializer(itr_record)
            elif technologies:
                dt=technology_serializer(itr_record)

            records_list.append(dt)
        page = '/datefilter'
        app.logger.info(f"Returning Records from {from_date} to {to_date}")
        return jsonify(status=200, data=get_paginated_list(records_list, page, start=request.args.get('start', 1),
                                                           limit=request.args.get('limit', 3)),
                       message=f"Returning Records from {from_date} to {to_date}")


