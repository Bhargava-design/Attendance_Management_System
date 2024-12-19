from django.db import models

class Employee(models.Model):
    username = models.CharField(max_length=50)
    empid = models.CharField(max_length=10, primary_key=True)
    firstname = models.CharField(max_length=50)
    lastname = models.CharField(max_length=50)
    emailid = models.EmailField(max_length=100)
    password = models.CharField(max_length=100)
    is_superuser = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.empid:
            last_emp = Employee.objects.order_by('-empid').first()
            if last_emp:
                last_number = int(last_emp.empid[3:5])
            else:
                last_number = 0
            self.empid = f"EMP{str(last_number + 1).zfill(2)}S"
        super().save(*args, **kwargs)

class QRCode(models.Model):
    QRCode_id = models.CharField(max_length=6, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    type = models.CharField(max_length=10, choices=[('login', 'Login'), ('logout', 'Logout')], default='logout')

class Attendance(models.Model):
    username = models.CharField(max_length=50)
    timestamps = models.DateTimeField(auto_now_add=True)
    activity = models.CharField(max_length=10, choices=[('login', 'Login'), ('logout', 'Logout')], default="logout")
    empid_id = models.CharField(max_length=10, default="EMP00S")  # Ensure this matches the actual column name in the database

    def __str__(self):
        return f"{self.username} - {self.activity} - {self.timestamps}"
    
class Activity(models.Model):
    username = models.CharField(max_length=50)
    empid = models.ForeignKey(Employee, on_delete=models.CASCADE)
    date = models.DateField()
    hours_spent = models.DecimalField(max_digits=5, decimal_places=2)