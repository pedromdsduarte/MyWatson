from django.urls import path
from django.conf.urls import url
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.decorators import login_required
from django.views.static import serve

from . import views



handler404 = 'mywatson.views.handler404'
handler500 = 'mywatson.views.handler500'
app_name = 'mywatson'
urlpatterns = [
    path('', login_required(views.GalleryView.as_view()), name='index'),
    path('upload/', login_required(views.upload_photo), name='upload_photo'),
    path('<int:pk>/', login_required(views.DetailView.as_view()), name='photo'),
    path('results', login_required(views.QueryResultsView.as_view()), name='query'),
    path('<int:pk>/add-tag', login_required(views.AddTagView.as_view()), name='add_tag'),
    # path('people', login_required(views.ClusterView.as_view()), name='people'),
    path('people', login_required(views.ClusterView.as_view()), name='people'),
    path('get_people', login_required(views.get_people), name='get_people'),
	url(r'^media/(?P<path>.*)$', serve,{'document_root': settings.MEDIA_ROOT}),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
