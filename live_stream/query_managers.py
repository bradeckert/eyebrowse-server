from django.db.models import Q
from django.db.models import Sum

from api.models import *

from live_stream.renderers import *

from accounts.models import *

from common.pagination import paginator

from datetime import timedelta

from common.templatetags.filters import url_domain
from django.utils import timezone
import operator

def live_stream_query_manager(get_dict, req_user, return_type="html"):

    valid_params = ["timestamp", "query", "following", "firehose", "direction", "filter", "ping", "req_user", "username", "limit", "orderBy", "start_time", "end_time"]

    valid_types = {
        "ping" : {
            "timestamp" : get_dict.get("timestamp", timezone.now()),
            "type" : "ping",
        },
    }
    
    search_params = {}
    for k, v in get_dict.items():
        if k in valid_params:
            search_params[k] = v
    
    type = get_dict.get("type", None)
    if type in valid_types:
        search_params = dict(search_params, **valid_types[type])

    hist = history_search(req_user, **search_params)
    
    page = get_dict.get("page", 1)

    history = paginator(page, hist)

    if req_user.is_authenticated():
        following = set(req_user.profile.follows.all())
    else:
        following = set([])
    
    if hasattr(history, 'object_list'):
        history.object_list = group_history(history.object_list)
    

    return hist, history_renderer(req_user, history, return_type,  get_dict.get("template"), get_params=search_params, following=following)



def history_search(req_user, timestamp=None, query=None, filter="following", type=None, direction="hl", orderBy="start_time", limit=None, username=None, start_time=None, end_time=None):

    history = EyeHistory.objects.all()
    try:
        
        if query:
            history = history.filter(Q(title__icontains=query) | Q(url__icontains=query))
            # print history.count(), "query"
        
        if filter == "following" and req_user.is_authenticated():
            history = req_user.profile.get_following_history(history=history)
            # print history.count(), "filter"
        
        if username:
            history = history.filter(user__username=username)
            # print history.count(), "username"
        
        orderBy = "-" + orderBy
        if direction == "lh":
            orderBy = orderBy[1:]
        history = history.order_by(orderBy)

        if start_time and end_time:
            history = history.filter(start_time__gt=start_time, end_time__lt=end_time)
            # print history.count(), "start/end", start_time, end_time
        
        #ping data with latest time and see if time is present
        ## must be last

        #print type, timestamp
        
        if type == "ping" and timestamp:
            history = history.filter(start_time__gt=timestamp)
            #print history.count(), "ping"

        if limit:
            history = history[:limit]
            # print history.count(), "limit"
            
    except Exception as e:
        print "EXCEPTION", e
        history = EyeHistory.objects.none()

    return history.select_related()

def profile_stat_gen(profile_user, username=None, url=None):
    """
        Helper to calculate total time spent for a given user.
        If a url is present, the queryset is filtered to reduce the set to only this url
    """
    if username is None:
        username = profile_user.username

    history_items = history_search(profile_user, filter="", username=username)

    if url:
        history_items = history_items.filter(url=url)

    total_time = history_items.aggregate(total=Sum("total_time"))

    return total_time["total"], history_items.count()


def online_user_count(filter_user=None):
    """
        Returns the number of users online
    """
    return len(_online_users())


def online_user(user):
    """
        Returns boolean if a user is online
    """
    return user in _online_users()


def _online_users():
    """
        Computes all of the users from the history items from the last 5 minutes
    """
    timestamp =  timezone.now() - timedelta(minutes=5)

    history = EyeHistory.objects.filter(start_time__gt=timestamp).select_related()

    users = set()
    for h in history:
        if not h.user in users:
            users.add(h.user)
    return users



def group_history(history):
    history = list(history)
    history_groups = []
    i = 0
    while i < len(history):
        group = GroupHistory(history[i])
        j = i + 1
        while j < len(history):
            if group.domain == history[j].domain and group.user == history[j].user:
                group.add_item(history[j])
                j += 1
            else:
                i = j
                break
        i = j
        history_groups.append(group)
        
    return history_groups


    
class GroupHistory(object):
    def __init__(self, history_item):
        self.id = history_item.id
        self.domain = history_item.domain
        history_item.messages = history_item.eyehistorymessage_set.all()
        self.history_items = [history_item]
        self.favIconUrl = history_item.favIconUrl
        self.user = history_item.user
    
    def add_item(self, history_item):
        history_item.messages = history_item.eyehistorymessage_set.all()
        self.history_items.append(history_item)
    
    def get_items(self):
        if len(self.history_items) == 1:
            return []
        else:
            return self.history_items[1:]
    
    def first_item(self):
        return self.history_items[0]
    

