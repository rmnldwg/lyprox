from django.contrib import admin

from .models import Institution, User

admin.site.register(User)
admin.site.register(Institution)
