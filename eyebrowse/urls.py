from django.conf.urls import patterns, include, url
from django.shortcuts import HttpResponse
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from django.conf import settings

from tastypie.api import Api
from api.resources import *
from eyebrowse.views import *

v1_api = Api(api_name='v1')
v1_api.register(UserResource())
v1_api.register(UserProfileResource())
v1_api.register(WhiteListItemResource())
v1_api.register(BlackListItemResource())
v1_api.register(EyeHistoryResource())
v1_api.register(EyeHistoryMessageResource())
v1_api.register(ChatMessageResource())

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),

    url(r'', include('django.contrib.auth.urls')),
    url(r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT}),
    url(r'^robots\.txt$', lambda r: HttpResponse("User-agent: *\nDisallow: /", mimetype="text/plain")),

    url(r'^users/(?P<username>.+)$', 'stats.views.profile_data'),
    url(r'^following/(?P<username>.+)$', 'stats.views.following_data'),
    url(r'^followers/(?P<username>.+)$', 'stats.views.followers_data'),
    
    url(r'^notifications', 'stats.views.notifications'),

    url(r'^accounts/', include('accounts.urls')),
    url(r'^live_stream/', include('live_stream.urls')),
    url(r'^stats/', include('stats.urls')),
    url(r'^api/', include('api.urls')),
    url(r'^api/', include(v1_api.urls)),

    url(r'^about', about),
    url(r'^faq', faq),
    url(r'^api_docs', api_docs),
    
    url(r'^consent_accept$', consent_accept),
    url(r'^consent$', consent),

    url(r'^ext/', include("extension.urls")),
)

urlpatterns += patterns('eyebrowse.views',
    url(r'^google3a0cf4e7f8daa91b.html$', 'google_verify'),
    url(r'^feedback$', 'feedback'),
    url(r'^downloads$', 'downloads'),
    url(r'^$', 'home'),
)
