from django.conf.urls import patterns, include, url

from django.contrib import admin
from tasks import settings
from django.conf.urls.static import static

admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'tasks.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    (r'^summernote/', include('django_summernote.urls')),
    url(r'', include(admin.site.urls)),
) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
