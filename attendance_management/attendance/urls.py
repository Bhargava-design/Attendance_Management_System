from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    login, register, AttendanceView, EmployeeViewSet, QRCodeViewSet, display_qrcode,
    AttendanceViewSet, ActivityViewSet, generate_qrcode, validate_qrcode, get_qrcode
)

router = DefaultRouter()
router.register(r'employees', EmployeeViewSet)
router.register(r'qrcodes', QRCodeViewSet)
router.register(r'attendance', AttendanceViewSet)
router.register(r'activity', ActivityViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('attendance/', AttendanceView.as_view(), name='attendance'),
    path('generate-qrcode/', generate_qrcode, name='generate-qrcode'),
    path('generate-qrcode/<str:qrcode_id>/', display_qrcode, name='display-qrcode'),
    path('validate-qrcode/', validate_qrcode, name='validate-qrcode'),
    path('register/', register, name='register'),
    path('login/', login, name='login'),
    path('qrcodes/<str:qrcode_id>/', get_qrcode, name='get-qrcode'),  # Add this line
]