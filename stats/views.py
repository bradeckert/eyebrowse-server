from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404

from annoying.decorators import render_to

from api.models import EyeHistory

from stats.models import FavData

from live_stream.query_managers import *

from common.view_helpers import _template_values, _get_query

from common.pagination import paginator

from common.constants import *

@login_required
@render_to('stats/follow_data.html')
def following_data(request, username=None):
    
    if request.user.username == username:
        username = None
    
    username, follows, profile_user, empty_search_msg = _profile_info(request.user, username, following=True)

    ## stats
    tot_time, item_count = profile_stat_gen(profile_user)

    fav_data = FavData.objects.get(user=profile_user)

    num_history = EyeHistory.objects.filter(user=profile_user).count()

    is_online = online_user(user=profile_user)
    
    following_users = profile_user.profile.follows.all()
    
    following_count = following_users.count()
    follower_count = UserProfile.objects.filter(follows=profile_user.profile).count()
    
    follow = follow_list(following_users, profile_user, empty_search_msg)
    

    template_dict = {
        'username': profile_user.username,
        'following_count': following_count,
        'follower_count': follower_count,
        "profile_user" : profile_user,
        "empty_search_msg" : empty_search_msg,
        "follows" : str(follows), 
        "is_online" : is_online,
        'follow_list': follow,
        "num_history" : num_history,
        "tot_time" : tot_time,
        "item_count" : item_count,
        "fav_data" : fav_data,
    }

    return _template_values(request, page_title="following list", navbar='nav_profile', sub_navbar="subnav_data", **template_dict)

    

@login_required
@render_to('stats/follow_data.html')
def followers_data(request, username=None):
    
    if request.user.username == username:
        username = None
    
    username, follows, profile_user, empty_search_msg = _profile_info(request.user, username, followers=True)

    ## stats
    tot_time, item_count = profile_stat_gen(profile_user)

    fav_data = FavData.objects.get(user=profile_user)

    num_history = EyeHistory.objects.filter(user=profile_user).count()

    is_online = online_user(user=profile_user)
    
    followers = UserProfile.objects.filter(follows=profile_user.profile)
    
    following_count = profile_user.profile.follows.count()
    follower_count = followers.count()
    
    follow = follow_list(followers, profile_user, empty_search_msg)
    

    template_dict = {
        'username': profile_user.username,
        'following_count': following_count,
        'follower_count': follower_count,
        "profile_user" : profile_user,
        "empty_search_msg" : empty_search_msg,
        "follows" : str(follows), 
        "is_online" : is_online,
        'follow_list': follow,
        "num_history" : num_history,
        "tot_time" : tot_time,
        "item_count" : item_count,
        "fav_data" : fav_data,
    }

    return _template_values(request, page_title="following list", navbar='nav_profile', sub_navbar="subnav_data", **template_dict)

    


@login_required
@render_to('stats/profile_data.html')
def profile_data(request, username=None):
    """
        Own profile page
    """
    username, follows, profile_user, empty_search_msg = _profile_info(request.user, username)

    get_dict, query, date = _get_query(request)

    get_dict["orderBy"] = "end_time"
    get_dict["direction"] = "hl"
    get_dict["filter"] = ""
    get_dict["page"] = request.GET.get("page", 1)
    get_dict["username"] = profile_user.username

    history_stream = live_stream_query_manager(get_dict, profile_user)

    ## stats
    tot_time, item_count = profile_stat_gen(profile_user)

    fav_data = FavData.objects.get(user=profile_user)

    num_history = EyeHistory.objects.filter(user=profile_user).count()

    is_online = online_user(user=profile_user)
    
    following_count = profile_user.profile.follows.count()
    follower_count = UserProfile.objects.filter(follows=profile_user.profile).count()
    

    template_dict = {
        'username': profile_user.username,
        'following_count': following_count,
        'follower_count': follower_count,
        "profile_user" : profile_user,
        "history_stream" : history_stream,
        "empty_search_msg" : empty_search_msg,
        "follows" : str(follows), 
        "is_online" : is_online,
        "num_history" : num_history,
        "tot_time" : tot_time,
        "item_count" : item_count,
        "fav_data" : fav_data,
        "query" : query,
        "date" : date,
    }

    return _template_values(request, page_title="profile history", navbar='nav_profile', sub_navbar="subnav_data", **template_dict)

def _profile_info(user, username=None, following=False, followers=False):
    """
        Helper to give basic profile info for rendering the profile page or its child pages
    """

    follows = False
    if not username: #viewing own profile
        username = user.username
        if following:
            msg_type = 'self_following'
        elif followers:
            msg_type = 'self_followers'
        else:
            msg_type = 'self_profile_stream'
        
    else:
        follows = user.profile.follows.filter(user__username=username).exists()
        if following:
            msg_type = 'following'
        elif followers:
            msg_type = 'followers'
        else:
            msg_type = 'profile_stream'
        
    empty_search_msg = EMPTY_SEARCH_MSG[msg_type]

    profile_user = get_object_or_404(User, username=username)

    return username, follows, profile_user, empty_search_msg


def follow_list(follows, req_user, empty_search_msg):

    template_values =  {
        'following' : follows,
        'user' : req_user,
        'empty_search_msg': empty_search_msg,
    }


    return render_to_string('stats/follow_list.html',template_values)
