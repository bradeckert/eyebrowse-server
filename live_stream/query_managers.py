from api.models import *

from live_stream.renderers import *

from accounts.models import *

from django.db.models import Q



def live_stream_query_manager(get_dict, user, return_type="html"):

    valid_params = ['timestamp', 'query', 'following', 'firehose', 'search', 'direction', 'ping', 'user', 'limit']

    valid_types = {
        'ping' : {
            'timestamp' : get_dict.get('timestamp', None),
            'type' : 'ping',
        },
    }
    
    search_params = {k : v for k, v in get_dict.items() if k in valid_params}
    
    type = get_dict.get('type', None)
    if type in valid_types:
        search_params = dict(search_params, **valid_types[type])

    history = history_search(**search_params)
    following = user.profile.follows.all()

    for h_item in history:
        h_item.follows = h_item.user in following
    return history_renderer(user, history, return_type, get_dict.get('page',1))



def history_search(timestamp=None, query=None, filter='firehose', type=None, direction='hl', orderBy="start_time", limit=None, user=None):

    history = EyeHistory.objects.all()
    
    try:
        #ping data with latest id and see if new id is present
        if type == 'ping' and timestamp:
            history = history.filter(start_time__gt=timestamp)

        if query:
            history = history.filter(Q(title__contains=query) | Q(url__contains=query))

        if filter == 'following' and user:
            history = user.get_following_history(history=history)

        orderBy = "-" + orderBy
        if direction == 'lh':
            orderBy = orderBy[1:]
        history = history.order_by(orderBy)

        if limit:
            history = history[:limit]
            
    except Exception as e:
        raise Exception(e)
        history = EyeHistory.objects.all()

    return history.select_related()