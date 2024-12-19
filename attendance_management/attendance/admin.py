from django.contrib import admin
from .models import QRCode, Employee, Activity, Attendance
# Register your models here.

admin.site.register(QRCode)

admin.site.register(Employee)

admin.site.register(Activity)

admin.site.register(Attendance)