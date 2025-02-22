from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Api Version 1
    path(
        "api/v1/",
        include(
            [
                
            ]
        ),
    ),

]
