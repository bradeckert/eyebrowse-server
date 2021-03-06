from django.contrib.sessions.models import Session
from django.contrib.auth.models import User
from django.conf.urls import url
from django.core.exceptions import MultipleObjectsReturned
from django.core.management import call_command
from django.db.models import Q

from tastypie.resources import ModelResource, ALL, ALL_WITH_RELATIONS
from tastypie.authorization import Authorization
from tastypie.authentication import BasicAuthentication
from tastypie.authorization import DjangoAuthorization
from tastypie import fields
from tastypie.paginator import Paginator

from api.defaults import DEFAULT_BLACKLIST
from accounts.models import UserProfile
from api.models import *
from resource_helpers import *
from defaults import DEFAULT_BLACKLIST
from eyebrowse.log import logger

import pytz

from common.templatetags.filters import url_domain
from common.templatetags.gravatar import gravatar_for_user

class MyBasicAuthentication(BasicAuthentication):
    def __init__(self, *args, **kwargs):
        super(MyBasicAuthentication, self).__init__(*args, **kwargs)

    def is_authenticated(self, request, **kwargs):
        if 'sessionid' in request.COOKIES:
            s = Session.objects.filter(pk=request.COOKIES['sessionid'])
            if s.exists():
                s = s[0]
                if '_auth_user_id' in s.get_decoded():
                    u = User.objects.get(id=s.get_decoded()['_auth_user_id'])
                    request.user = u
                    return True 
        return False

class PublicGetAuthentication(MyBasicAuthentication):
    def is_authenticated(self, request, **kwargs):

        if request.method == "GET":
            return True
        else:
            return super(PublicGetAuthentication, self).is_authenticated(request, **kwargs)

class BaseMeta:
    """
        Abstract class to get basic authentication and authorization.
    """
    authentication = MyBasicAuthentication()
    authorization = DjangoAuthorization()
    serializer = urlencodeSerializer()

class BaseResource(ModelResource):
    """
        Subclass this to get generic ModelResource add-ins that TastyPie doesn't supply.
    """
    def apply_authorization_limits(self, request, object_list):
        return object_list.filter(user=request.user) 

class UserResource(ModelResource):

    def override_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<username>[\w\d_.-]+)/$" % self._meta.resource_name, self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
        ]

    class Meta(BaseMeta):
        queryset = User.objects.all()
        resource_name = 'user'
        
        detail_allowed_methods = ['get']
        list_allowed_methods = []
        fields = ['username', 'first_name', 'last_name', 'last_login']

        filtering = {
            'username': ALL,
        }

class UserProfileResource(ModelResource):

    user = fields.ForeignKey(UserResource, 'user')

    class Meta(BaseMeta):
        queryset = UserProfile.objects.all()
        resource_name = 'user_profile'

        detail_allowed_methods = ['get']
        list_allowed_methods = []
        fields = ['pic_url']
        filtering = {
            'user' : ALL_WITH_RELATIONS
        }

class FilterSetItemResource(BaseResource):
    """
        Abstract base class
    """
    user = fields.ForeignKey(UserResource, 'user')  
    
    class Meta(BaseMeta):

        detail_allowed_methods = ['get', 'post', 'put', 'delete']
        filtering = {
            'user': ALL_WITH_RELATIONS,
            'date_created': ALL,
            'url' : ALL,
        }
        resource_name = 'filterset'


class WhiteListItemResource(FilterSetItemResource):

    def obj_create(self, bundle, request=None, **kwargs):
        url = bundle.data['url']
        
        blacklist_item = get_BlackListItem(url) #check to see if this exists
        if blacklist_item:
            blacklist_item.delete()

        #do not create if it is a default blacklist url
        if url in DEFAULT_BLACKLIST:
            return bundle

        try:
            obj = WhiteListItem.objects.get(user=request.user, url=url)
        except WhiteListItem.DoesNotExist:
            return super(WhiteListItemResource, self).obj_create(bundle, request, user=request.user, **kwargs)
        except MultipleObjectsReturned: 
            #multiple items created, delete duplicates
            call_command("remove_duplicate_filtersets")
        return bundle

    class Meta(FilterSetItemResource.Meta):

        queryset = WhiteListItem.objects.select_related().all()
        resource_name = 'whitelist'

class BlackListItemResource(FilterSetItemResource):
    
    def obj_create(self, bundle, request=None, **kwargs):

        url = bundle.data['url']

        whitelist_item = get_WhiteListItem(url) #check to see if this exists
        if whitelist_item:
            whitelist_item.delete()
        try:
            obj = BlackListItem.objects.get(user=request.user, url=url)
        except BlackListItem.DoesNotExist:
            return super(BlackListItemResource, self).obj_create(bundle, request, user=request.user, **kwargs)        
        except MultipleObjectsReturned:
            #multiple items created, delete duplicates
            call_command("remove_duplicate_filtersets")
        return bundle

    class Meta(FilterSetItemResource.Meta):

        queryset = BlackListItem.objects.select_related().all()
        resource_name = 'blacklist'


class EyeHistoryMessageResource(ModelResource):
    
    def apply_authorization_limits(self, request, object_list):
        return object_list.filter(eyehistory__user=request.user) 
    
    class Meta(BaseMeta):
        queryset = EyeHistoryMessage.objects.all()
        resource_name = 'history-message'
        
        list_allowed_methods = ['get']
        detail_allowed_methods = ['get']

class EyeHistoryResource(ModelResource):
    user = fields.ForeignKey(UserResource, 'user')
    message = fields.ToManyField(EyeHistoryMessageResource, 'eyehistorymessage_set', null=True, blank=True, full=True)

    class Meta(BaseMeta):
        queryset = EyeHistory.objects.select_related().all().order_by('-start_time')
        resource_name = 'history-data'

        list_allowed_methods = ['get', 'post']
        detail_allowed_methods = ['get', 'post', 'put', 'delete']
        filtering = {
            'user': ALL_WITH_RELATIONS,
            'url' : ALL,
            'title' : ALL,
            'start_time' : ALL,
            'end_time' : ALL,
            'total_time' : ALL,
        }
        paginator_class = Paginator
        authentication = PublicGetAuthentication()
        
    def dehydrate(self, bundle):
        bundle.data['username'] = bundle.obj.user.username
        bundle.data['pic_url'] = gravatar_for_user(User.objects.get(username=bundle.obj.user.username))
        return bundle


    def obj_create(self, bundle, request=None, **kwargs):

        url = bundle.data['url']
        domain = url_domain(url)
          
        bundle.data["domain"] = domain
  
        title = bundle.data['title']
        start_time = bundle.data['start_time']
        start_event = bundle.data['start_event']
        end_time = bundle.data['end_time']
        end_event = bundle.data['end_event']
        favIconUrl = bundle.data.get('favIconUrl')
        src = bundle.data['src']
        
        end_time = datetime.datetime.strptime(end_time, '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=pytz.utc)
        start_time = datetime.datetime.strptime(start_time, '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=pytz.utc)
        
        message = bundle.data.get('message')
        
        if message and message.strip() == '':
            message = None
            
        if message:
            bundle.data.pop('message', None)

        try:
            exists = EyeHistory.objects.filter(user=request.user, url=url, title=title, src=src, favIconUrl=favIconUrl, start_time__gt=start_time-datetime.timedelta(minutes=1), start_event=start_event)
            if exists.count() > 0:
                eye_his = exists[0]
                eye_his.end_time = end_time
                eye_his.end_event = end_event
                elapsed_time = end_time - start_time
                eye_his.total_time = int(round((elapsed_time.microseconds / 1.0E3) + (elapsed_time.seconds * 1000) + (elapsed_time.days * 8.64E7)))
                eye_his.humanize_time = humanize_time(elapsed_time)
                eye_his.save()
                if message:
                    eye_message, created = EyeHistoryMessage.objects.get_or_create(eyehistory=eye_his, message=message)
            else:
               # save_raw_eyehistory(request.user, url, title, start_event, end_event, start_time, end_time, src, domain, favIconUrl)
                dup_histories = EyeHistory.objects.filter(user=request.user, url=url, title=title, end_time__gt=start_time-datetime.timedelta(minutes=5))
                if dup_histories.count() > 0:
                    obj = merge_histories(dup_histories, end_time, end_event)
                    if message:
                        eye_message, created = EyeHistoryMessage.objects.get_or_create(eyehistory=obj, message=message)
                else:
                    bundle_res = super(EyeHistoryResource, self).obj_create(bundle, request, user=request.user, **kwargs)
                    if message:
                        eye_message, created = EyeHistoryMessage.objects.get_or_create(eyehistory=bundle_res.obj, message=message)
                    return bundle_res;
        except Exception, e:
            logger.exception(e)
  
        except MultipleObjectsReturned:
            #multiple items created, delete duplicates
            call_command("remove_duplicate_history")
         
        return bundle



class ChatMessageResource(ModelResource):
    
    author = fields.ForeignKey(UserResource, 'author')
    
    def dehydrate(self, bundle):
        bundle.data['author'] = bundle.obj.author.username
        return bundle

    class Meta(BaseMeta):
        queryset = ChatMessage.objects.select_related().all()
        resource_name = 'chatmessages'

        list_allowed_methods = ['get', 'post']
        detail_allowed_methods = ['get', 'post', 'put', 'delete']
        excludes = ['id']
        filtering = {
            'author': ALL_WITH_RELATIONS,
            'url' : ALL,
            'date' : ALL,
            'messages': ALL,
        }

    def apply_filters(self, request, applicable_filters):
        base_object_list = super(ChatMessageResource, self).apply_filters(request, applicable_filters)
        return base_object_list

    def obj_create(self, bundle, request=None, **kwargs):
        try:
            bundle.data['date'] = datetime.datetime.strptime(bundle.data['date']['_d'], '%Y-%m-%dT%H:%M:%S.%fZ')
            val = super(ChatMessageResource, self).obj_create(bundle, request, **kwargs)
        except Exception, e:
            logger.exception(e)
        return val
    
