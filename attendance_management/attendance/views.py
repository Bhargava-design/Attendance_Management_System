from .models import Employee, QRCode, Attendance, Activity
from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import EmployeeSerializer, QRCodeSerializer, AttendanceSerializer, ActivitySerializer
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework.views import APIView
import random
import qrcode
from django.http import HttpResponse
from io import BytesIO
from django.shortcuts import render

class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer

    # Allow filtering by username
    def get_queryset(self):
        queryset = Employee.objects.all()
        username = self.request.query_params.get('username')
        if username:
            queryset = queryset.filter(username=username)
        return queryset

class QRCodeViewSet(viewsets.ModelViewSet):
    queryset = QRCode.objects.all()
    serializer_class = QRCodeSerializer

class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer

class ActivityViewSet(viewsets.ModelViewSet):
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer

class AttendanceView(APIView):
    def post(self, request, format=None):
        serializer = AttendanceSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
@api_view(['POST'])
def register(request):
    username = request.data.get('username')
    firstname = request.data.get('firstname')
    lastname = request.data.get('lastname')
    emailid = request.data.get('emailid')
    password = request.data.get('password')
    print(request.data)

    # Validate emailid
    if emailid is None:
        return Response(
            {"error": "Email ID is required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Check if the email domain is @Station-S.com or @station-s.com
    is_superuser = emailid.lower().endswith("@station-s.com")

    # Create user in auth_user table
    user = User.objects.create_user(username=username, email=emailid, password=password)
    user.first_name = firstname
    user.last_name = lastname
    user.is_superuser = is_superuser
    user.save()

    # If the user is not a superuser, create user in attendance_employee table
    if not is_superuser:
        employee = Employee(
            username=username,
            firstname=firstname,
            lastname=lastname,
            emailid=emailid,
            password=password,
            is_superuser=is_superuser
        )
        employee.save()

    serializer = EmployeeSerializer(employee) if not is_superuser else EmployeeSerializer(
        Employee(
            username=username,
            firstname=firstname,
            lastname=lastname,
            emailid=emailid,
            password=password,
            is_superuser=is_superuser
        )
    )
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
def login(request):
    username = request.data.get('username')
    password = request.data.get('password')
    
    # Authenticate user using Django's built-in authentication system
    user = authenticate(username=username, password=password)

    if user is not None:
        # User is authenticated, return user details
        return Response({
            'username': user.username,
            'id': user.id,
            'email': user.email,
            'is_superuser': user.is_superuser
        }, status=status.HTTP_200_OK) 
    else:
        # User is not authenticated, return error
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['POST'])
def generate_qrcode(request):
    qrcode_type = request.data.get('type', 'login')
    qrcode_id = '{:06d}'.format(random.randint(0, 999999))

    # Check if there is an active QR code of the same type
    active_qrcode = QRCode.objects.filter(type=qrcode_type, is_active=True).first()
    if active_qrcode:
        # Check if the active QR code is already active
        if active_qrcode.is_active:
            # Return the active QR code details
            serializer = QRCodeSerializer(active_qrcode)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            # Update the active QR code to inactive
            active_qrcode.is_active = False
            active_qrcode.save()

    # Create a new QR code
    qrcode_obj = QRCode.objects.create(QRCode_id=qrcode_id, type=qrcode_type)
    serializer = QRCodeSerializer(qrcode_obj)

    # Generate QR code image
    img = generate_qr_image(qrcode_id)
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    response = HttpResponse(buffer, content_type="image/png")
    response['Content-Disposition'] = f'attachment; filename="qrcode_{qrcode_type}.png"'
    return response

def display_qrcode(request, qrcode_id):
    try:
        # Fetch the QR code by QRCode_id
        qrcode_obj = QRCode.objects.get(QRCode_id=qrcode_id)
        serializer = QRCodeSerializer(qrcode_obj)

        # Generate QR code image
        img = generate_qr_image(qrcode_id)
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        response = HttpResponse(buffer, content_type="image/png")
        response['Content-Disposition'] = f'attachment; filename="qrcode_{qrcode_obj.type}.png"'
        return response
    except QRCode.DoesNotExist:
        return Response({'error': 'QR code not found'}, status=status.HTTP_404_NOT_FOUND)
    except QRCode.MultipleObjectsReturned:
        return Response({'error': 'Multiple QR codes found for the given ID'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(['POST'])
def validate_qrcode(request):
    qrcode_id = request.data.get('qrcode_id')
    qrcode_type = request.data.get('type')

    if not qrcode_id or not qrcode_type:
        return Response({'error': 'Missing qrcode_id or type'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        qrcode = QRCode.objects.get(QRCode_id=qrcode_id, type=qrcode_type, is_active=True)
        qrcode.is_active = True  # Mark the QR code as inactive after validation
        qrcode.save()
        return Response({'valid': True, 'message': 'QR code is valid'}, status=status.HTTP_200_OK)
    except QRCode.DoesNotExist:
        return Response({'valid': False, 'message': 'Invalid QR code or type mismatch'}, status=status.HTTP_400_BAD_REQUEST)
    
def generate_qr_image(data):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white")

@api_view(['GET'])
def get_qrcode(request, qrcode_id):
    try:
        # Fetch the QR code by QRCode_id
        qrcode_obj = QRCode.objects.get(QRCode_id=qrcode_id)
        serializer = QRCodeSerializer(qrcode_obj)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except QRCode.DoesNotExist:
        # Return 404 if the QR code doesn't exist
        return Response({"error": "QR code not found"}, status=status.HTTP_404_NOT_FOUND)