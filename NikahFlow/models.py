from django.db import models
from django.core.validators import FileExtensionValidator, MinValueValidator, MaxValueValidator
import uuid


class User(models.Model):
    ROLE_CHOICES = [
        ('bridegroom', 'Bride/Groom'),
        ('imam', 'Assistant Registrar'),
        ('adminchairman', 'Admin Chairman'),
    ]
    

    # Add this new field for identification number
    id_number = models.CharField(max_length=14,unique=True)
    role = models.CharField(max_length=30, choices=ROLE_CHOICES)
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, unique=True)
    fullname = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=20)
    password = models.CharField(max_length=128)
    status = models.CharField(max_length=20, default='Active')
    created_at = models.DateTimeField(auto_now_add=True)
    userid = models.CharField(max_length=50, null=True, blank=True)
    remarks = models.CharField(max_length=100)

    def __str__(self):
        return self.username
    
    def get_role_display(self):
        return dict(self.ROLE_CHOICES).get(self.role, self.role)
        
    def get_status_display(self):
        if not self.status:
            return 'Active'
        return dict(self.STATUS_CHOICES).get(self.status, self.status)
        

class BrideGroomApplication(models.Model):
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='applications',
        null=True  # Temporarily allow null for existing data
    )
    MARITAL_STATUS_CHOICES = [
        ('BUJANG', 'Bujang'),
        ('DUDA', 'Duda'),
        ('JANDA', 'Janda'),
    ]

    # Application metadata
    application_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, default='PENDING', choices=[
        ('PENDING', 'Pending'),
        ('REVIEWED', 'Reviewed'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ])

    remarks = models.CharField(max_length=100)
    # Groom Information
    groom_fullname = models.CharField(max_length=100)
    groom_id_number = models.CharField(max_length=20)
    groom_dob = models.DateField()
    groom_nationality = models.CharField(max_length=50)
    groom_religion = models.CharField(max_length=50)
    groom_marital_status = models.CharField(max_length=10, choices=MARITAL_STATUS_CHOICES)
    groom_address = models.TextField()

    # Groom Documents
    groom_ic_copy = models.FileField(
        upload_to='applications/groom/ic/',
        validators=[FileExtensionValidator(['pdf'])]
    )
    groom_hiv_test = models.FileField(
        upload_to='applications/groom/hiv/',
        validators=[FileExtensionValidator(['pdf'])]
    )
    groom_marriage_course = models.FileField(
        upload_to='applications/groom/course/',
        validators=[FileExtensionValidator(['pdf'])]
    )

    # Bride Information
    bride_fullname = models.CharField(max_length=100)
    bride_id_number = models.CharField(max_length=20)
    bride_dob = models.DateField()
    bride_nationality = models.CharField(max_length=50)
    bride_religion = models.CharField(max_length=50)
    bride_marital_status = models.CharField(max_length=10, choices=MARITAL_STATUS_CHOICES)
    bride_address = models.TextField()

    # Wali Information
    wali_name = models.CharField(max_length=100)
    wali_ic = models.CharField(max_length=20)

    # Bride Documents
    bride_ic_copy = models.FileField(
        upload_to='applications/bride/ic/',
        validators=[FileExtensionValidator(['pdf'])]
    )
    bride_hiv_test = models.FileField(
        upload_to='applications/bride/hiv/',
        validators=[FileExtensionValidator(['pdf'])]
    )
    bride_marriage_course = models.FileField(
        upload_to='applications/bride/course/',
        validators=[FileExtensionValidator(['pdf'])]
    )
    wali_ic_copy = models.FileField(
        upload_to='applications/wali/ic/',
        validators=[FileExtensionValidator(['pdf'])]
    )
    wali_consent = models.FileField(
        upload_to='applications/wali/consent/',
        validators=[FileExtensionValidator(['pdf'])]
    )

    def __str__(self):
        return f"Marriage Application: {self.groom_fullname} & {self.bride_fullname}"


class ImamAvailability(models.Model):
    imam = models.ForeignKey(User, on_delete=models.CASCADE, related_name='availabilities')
    date = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=[
            ('available', 'Available'),
            ('unavailable', 'Not Available'),
            ('pending', 'Pending Submission')
        ],
        default='pending'
    )
    time_slots = models.JSONField(default=list)  # Stores list of available times like ["09:00", "14:00"]
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('imam', 'date')
        ordering = ['date']

    def __str__(self):
        return f"{self.imam.username} - {self.date} ({self.status})"
    
class SolemnisationSlot(models.Model):
    date = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=[
            ('available', 'Available'),
            ('unavailable', 'Not Available'),
            ('pending', 'Pending Submission')
        ],
        default='pending'
    )
    time_slots = models.JSONField(default=list)  
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('status', 'date')
        ordering = ['date']

class SolemnisationBooking(models.Model):
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='bookings',
        null=True
    )
    groom_name = models.CharField(max_length=100, blank=True, null=True)
    bride_name = models.CharField(max_length=100, blank=True, null=True)
    booking_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    remarks = models.TextField(blank=True, null=True)

    status = models.CharField(max_length=20, default='PENDING', choices=[
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ])

    booking_date = models.DateField()
    time_slot = models.CharField(max_length=20)
    start_time = models.TimeField()
    end_time = models.TimeField()
    location = models.CharField(max_length=255)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user} - {self.booking_date} - {self.time_slot}"

class ImamSolemnisationSchedule(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    
    imam = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='solemnisation_assignments',
        limit_choices_to={'role': 'imam'}  # Ensure only imams can be assigned
    )
    booking = models.ForeignKey(
        SolemnisationBooking,
        on_delete=models.CASCADE,
        related_name='imam_assignments'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )
    remarks = models.TextField(blank=True, null=True)
    assigned_at = models.DateTimeField(auto_now_add=True)
   
    class Meta:
        unique_together = ('imam', 'booking')  # Prevent duplicate assignments
        verbose_name = "Imam Assignment"
        verbose_name_plural = "Imam Assignments"
    
    def __str__(self):
        return f"{self.imam.username} - {self.booking.booking_date} ({self.status})"
    
class MonthlyReport(models.Model):
    report_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="Report ID"
    )
    month = models.DateField(
        help_text="Month and year of the report (day will be ignored)"
    )
    total_applications = models.PositiveIntegerField(
        default=0,
        verbose_name="Total Applications"
    )
    approved_applications = models.PositiveIntegerField(
        default=0,
        verbose_name="Approved Applications"
    )
    solemnisation_count = models.PositiveIntegerField(
        default=0,
        verbose_name="Solemnisation Count"
    )
    admin = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='monthly_reports',
        limit_choices_to={'role': 'adminchairman'},
        verbose_name="Admin Chairman"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('month', 'admin')  # Ensure one report per admin per month
        ordering = ['-month']
        verbose_name = "Monthly Report"
        verbose_name_plural = "Monthly Reports"

    def __str__(self):
        return f"Monthly Report - {self.month.strftime('%B %Y')}"