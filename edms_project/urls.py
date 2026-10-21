from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
import os


@login_required
def protected_media(request, path):
    """Serve media files only to authenticated users."""
    file_path = os.path.join(settings.MEDIA_ROOT, path)
    if not os.path.exists(file_path):
        raise Http404
    return FileResponse(open(file_path, 'rb'))


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('documents.urls')),
    re_path(r'^media/(?P<path>.*)$', protected_media, name='protected_media'),
] + static(settings.STATIC_URL, document_root=settings.BASE_DIR / 'static')
