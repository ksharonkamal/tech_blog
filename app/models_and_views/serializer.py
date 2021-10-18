from .models import Technologies, User
import ast
from utils.update_like_dislike_count import update_like_dislike_count


def replace_with_ids(list_of_tech):
    ids_list=[]
    for itr_tech in list_of_tech:
        tech_id=Technologies.query.filter_by(name = itr_tech).first()
        if tech_id:
            ids_list.append(tech_id.id)
    ids_list = f"{ids_list}"
    return ids_list


def string_list_string(technology):
    tech_list = []

    technology = ast.literal_eval(technology)
    print("technology=", technology, type(technology))

    temp_str = technology[0]
    print("temp_str=", temp_str, type(temp_str))
    my_list = list(temp_str.split(", "))
    print("my_list=", my_list, type(my_list))

    for itr in my_list:
        print(itr, type(itr))
        tech = Technologies.query.filter_by(name=itr).first()
        tech_id = tech.id
        print(tech_id)
        tech_list.append(tech_id)
        print(tech_list)

    print("tech_list=", type(tech_list[0]))
    my_string = ','.join([str(x) for x in tech_list])
    print("my_string= ", my_string)
    return my_string


def user_serializer(user):
    technology = ast.literal_eval(user.technology)
    tech_list = []

    for itr in technology:
        tech_check = Technologies.query.filter_by(id=int(itr)).first()
        if tech_check:
            tech_list.append(tech_check.name)
    print(tech_list)

    dt = {
        'name': user.name,
        'user_id': user.id,
        'email': user.email,
        'mobile': user.mobile,
        'technology': tech_list,
        'role':user.roles,
        'updated_at':user.updated_at
    }
    return dt



def query_serializer(query_obj):
    dt = {
        'query_id':query_obj.id,
        'user_id':query_obj.u_id,
        'title':query_obj.title,
        'description':query_obj.description,
        # 'name':
        #'file_path':query_obj.file_path,
        'technology_id':query_obj.t_id,
        'updated_at':query_obj.updated_at
        #'status':query_obj.status
    }
    return dt


def comments_serializer(comments_obj):
    update_like_dislike_count(None)
    dt = {
        'user_id':comments_obj.u_id,
        'user_name':(User.query.filter_by(id=comments_obj.u_id).first()).name,
        'query_id': comments_obj.q_id,
        'msg':comments_obj.msg,
        'like_count':comments_obj.like_count,
        'dislike_count':comments_obj.dislike_count,
        'updated_at':comments_obj.updated_at
        #'status':comments_obj.status
    }
    return dt


def technology_serializer(tech_obj):
    dt={
        'tech_id':tech_obj.id,
        'name':tech_obj.name,
        'updated_at':tech_obj.updated_at
    }
    return dt