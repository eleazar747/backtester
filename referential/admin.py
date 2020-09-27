from django.contrib import admin
from .models import securitydescription
# Register your models here.
class SecurityDescriptionAdmin(admin.ModelAdmin):
   list_display   = ('yahoo_id', 'name')

# Register your models here.
admin.site.register(securitydescription,SecurityDescriptionAdmin)