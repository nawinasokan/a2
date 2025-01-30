from django.contrib import admin

from admin_dash.models import User

# Register your models here.
class UserRecordAdmin(admin.ModelAdmin):
    list_display = ('username', 'password', 'first_name', 'last_name', 'created_at', 'created_by','user_status')


admin.site.register(User,UserRecordAdmin)