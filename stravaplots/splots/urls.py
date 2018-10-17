from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^make_plot/$',views.make_plot,name='make_plot'),
    url(r'^make_image/(?P<n_recent>\w+)/(?P<year>\w+)/(?P<month>\w+)/(?P<day>\w+)$',views.make_image,name = 'make_image'),
    url(r'^authenticate/$',views.authenticate,name = 'authenticate'),
    url(r'^exchange/$',views.exchange,name='exchange'),
    url(r'^clear_session/$',views.clear_session,name = 'clear_session'),
]