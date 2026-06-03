
from django.shortcuts import render,redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth import authenticate, login as auth_login
from django.db.models import Sum, Q
from django.db import IntegrityError
from django.core.exceptions import PermissionDenied
from .models import ImamSolemnisationSchedule, MonthlyReport, User,BrideGroomApplication,ImamAvailability,SolemnisationSlot,SolemnisationBooking
from django.core.files.storage import FileSystemStorage
import uuid
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import datetime, timedelta, time
import calendar
# Create your views here.
VALID_ADMIN_IDS = {'adminmasjid0411'}
VALID_IMAM_IDS = {'imammasjid1104'}

def homepage(request):
    return render(request, "homepage.html")

def mainpage(request):
    return render(request,"mainpage.html")

def registration(request):
    if request.method == 'POST':
        role = request.POST.get('role')
        email = request.POST.get('email')
        username = request.POST.get('username')
        id_number = request.POST.get('id_number')
        fullname = request.POST.get('fullname')
        phone = request.POST.get('phonenumber')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        userid = request.POST.get('userid', '')  # Empty default if not provided

        # Validation
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect('registration')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return redirect('registration')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return redirect('registration')

        # Additional validation for admin/imam roles
        if role in ['adminchairman', 'imam']:
            if not userid:
                messages.error(request, "User ID is required for this role.")
                return redirect('registration')
            
            # Check if user ID is valid for the selected role
            if role == 'adminchairman' and userid not in VALID_ADMIN_IDS:
                messages.error(request, "Invalid Admin User ID.")
                return redirect('registration')
            
            if role == 'imam' and userid not in VALID_IMAM_IDS:
                messages.error(request, "Invalid Imam User ID.")
                return redirect('registration')

        # Save user with hashed password
        user = User(
            role=role,
            email=email,
            username=username,
            id_number=id_number,
            fullname=fullname,
            phone_number=phone,
            password=make_password(password),  # hashes password
            userid=userid if role in ['adminchairman', 'imam'] else None
        )
        user.save()

        return render(request, 'signup.html', {'show_popup': True})

    return render(request, 'signup.html')


def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        requested_role = request.POST.get('role')
        
        try:
            user = User.objects.get(username=username)
            
            # Manual password check
            if check_password(password, user.password):
                if user.role == requested_role:
                    request.session['user_id'] = user.id  # Simple session auth
                    request.session['user_role'] = user.role
                    
                    if user.role == 'adminchairman':
                        return redirect('admin_account')
                    elif user.role == 'imam':
                        return redirect('imam_account')
                    else:
                        return redirect('bridegroom_account')
                else:
                    messages.error(request, f"Please log in as {user.get_role_display()}")
            else:
                messages.error(request, "Invalid password")
        except User.DoesNotExist:
            messages.error(request, "Username not found")
        
        return redirect('signin')
    
    return render(request, 'signin.html')

def admin_account(request):
    if not request.session.get('user_id') or request.session.get('user_role') != 'adminchairman':
        return redirect('signin')
    
    try:
        admin_user = User.objects.get(id=request.session['user_id'])
        return render(request, 'accountpage-admin.html', {
            'user': admin_user,
            'role_display': admin_user.get_role_display()
        })
    except User.DoesNotExist:
        return redirect('signin')
    
def imam_account(request):
    if not request.session.get('user_id') or request.session.get('user_role') != 'imam':
        return redirect('signin')
    
    try:
        admin_user = User.objects.get(id=request.session['user_id'])
        return render(request, 'accountpage-imam.html', {
            'user': admin_user,
            'role_display': admin_user.get_role_display()
        })
    except User.DoesNotExist:
        return redirect('signin')
    
def bridegroom_account(request):
    if not request.session.get('user_id') or request.session.get('user_role') != 'bridegroom':
        return redirect('signin')
    
    try:
        admin_user = User.objects.get(id=request.session['user_id'])
        return render(request, 'accountpage-bride_groom.html', {
            'user': admin_user,
            'role_display': admin_user.get_role_display()
        })
    except User.DoesNotExist:
        return redirect('signin')


def logout(request):
    request.session.flush()
    messages.success(request, "Log out successfully!")
    return redirect('signin')



def user_management(request):
    # Admin authentication check
    if not request.session.get('user_id') or request.session.get('user_role') != 'adminchairman':
        return redirect('signin')
    
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('search', '')
    edit_user_id = request.GET.get('edit', '')
    
    # Base query - only bride/groom users
    users = User.objects.filter(
        role__in=['bride', 'groom', 'bridegroom']
    ).order_by('-created_at')
    
    # Apply filters
    if status_filter:
        users = users.filter(status=status_filter)
    
    if search_query:
        users = users.filter(
            Q(fullname__icontains=search_query) | 
            Q(email__icontains=search_query) |
            Q(username__icontains=search_query)
        )
    
    # Get user to edit if edit parameter exists
    user_to_edit = None
    if edit_user_id:
        try:
            user_to_edit = get_object_or_404(User, id=edit_user_id)
            # Ensure only editing bride/groom
            if user_to_edit.role not in ['bride', 'groom', 'bridegroom']:
                messages.error(request, 'Can only edit bride/groom profiles')
                return redirect('user_management')
        except:
            messages.error(request, 'User not found')
    
    context = {
        'users': users,
        'status_filter': status_filter,
        'search_query': search_query,
        'user_to_edit': user_to_edit,
    }
    return render(request, 'usermanagement.html', context)


def delete_user(request, user_id):
    if not request.session.get('user_id') or request.session.get('user_role') != 'adminchairman':
        return redirect('signin')

    try:
        user = get_object_or_404(User, id=user_id)
        fullname = user.fullname
        user.delete()
        messages.success(request, f'User {fullname} has been deleted successfully.')
    except Exception as e:
        messages.error(request, f'Error deleting user: {str(e)}')
    
    return redirect('user_management')

def edit_user(request, user_id):
    # Get the user object or return 404 if not found
    user = get_object_or_404(User, id=user_id)
    
    # Ensure only bride/groom users can be edited here
    if user.role != 'bridegroom':
        messages.error(request, "You can only edit bride/groom profiles here")
        return redirect('user_management')
    
    if request.method == 'POST':
        # Handle form submission
        id_number=request.POST.get('id_number')
        fullname = request.POST.get('fullname')
        username = request.POST.get('username')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone')
        password = request.POST.get('password')
        
        # Basic validation
        if not all([id_number, fullname, username, email, phone_number]):
            messages.error(request, "Please fill in all required fields")
            return render(request, 'edituserpage.html', {'user': user})
        
        # Check if username or email already exists (excluding current user)
        if User.objects.filter(username=username).exclude(id=user.id).exists():
            messages.error(request, "Username already exists")
            return render(request, 'edituserpage.html', {'user': user})
            
        if User.objects.filter(email=email).exclude(id=user.id).exists():
            messages.error(request, "Email already exists")
            return render(request, 'edituserpage.html', {'user': user})
        
        # Update user fields
        user.id_number = id_number
        user.fullname = fullname
        user.username = username
        user.email = email
        user.phone_number = phone_number

        # Only update password if a new one was provided
        if password:
            user.password = make_password(password)
        
        try:
            user.save()
            messages.success(request, "Bride/Groom profile updated successfully!")
            return redirect('user_management')
        except Exception as e:
            messages.error(request, f"Error updating user: {str(e)}")
    
    # For GET requests or if form submission fails
    return render(request, 'edituserpage.html', {
        'user': user,
        'status_display': user.status
    })

def create_user(request):
    if request.method == 'POST':
        # Get all form data
        role = request.POST.get('role')
        fullname = request.POST.get('fullname')
        id_number = request.POST.get('id_number')
        username = request.POST.get('username')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        # Basic validation
        required_fields = [role, fullname, id_number, username, email, phone_number, password, confirm_password]
        if not all(required_fields):
            messages.error(request, "Please fill in all required fields")
            return render(request, 'createuserpage.html')
        
        # Check if passwords match
        if password != confirm_password:
            messages.error(request, "Passwords do not match")
            return render(request, 'createuserpage.html')
        
        # Check if username or email already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return render(request, 'createuserpage.html')
            
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists")
            return render(request, 'createuserpage.html')
            
        if User.objects.filter(id_number=id_number).exists():
            messages.error(request, "ID Number already exists")
            return render(request, 'createuserpage.html')
        
        try:
            # Create new user
            new_user = User.objects.create(
                role=role,
                fullname=fullname,
                id_number=id_number,
                username=username,
                email=email,
                phone_number=phone_number,
                password=make_password(password)
            )
            
            messages.success(request, f"User {new_user.username} created successfully!")
            return redirect('user_management')
            
        except Exception as e:
            messages.error(request, f"Error creating user: {str(e)}")
            return render(request, 'createuserpage.html')
    
    # For GET requests
    return render(request, 'createuserpage.html')


def submit_application(request):
    if not request.session.get('user_id'):
        messages.error(request, 'You need to login to submit an application')
        return redirect('signin')  # Redirect to your login page
    try:
        user = User.objects.get(id=request.session['user_id'])
    except User.DoesNotExist:
        messages.error(request, 'User not found')
        return redirect('login')
    if request.method == 'POST':
        try:
            # Create new application instance
            application = BrideGroomApplication()

            # Associate with logged-in user
            application.user = user

            # Set application metadata
            application.application_id = uuid.uuid4()
            application.status = 'PENDING'
            
            # Process groom information
            application.groom_fullname = request.POST.get('groom_fullname')
            application.groom_id_number = request.POST.get('groom_id_number')
            application.groom_dob = request.POST.get('groom_dob')
            application.groom_nationality = request.POST.get('groom_nationality')
            application.groom_religion = request.POST.get('groom_religion')
            application.groom_marital_status = request.POST.get('groom_marital_status')
            application.groom_address = request.POST.get('groom_address')
            
            # Process groom documents
            if 'groom_ic_copy' in request.FILES:
                application.groom_ic_copy = request.FILES['groom_ic_copy']
            if 'groom_hiv_test' in request.FILES:
                application.groom_hiv_test = request.FILES['groom_hiv_test']
            if 'groom_marriage_course' in request.FILES:
                application.groom_marriage_course = request.FILES['groom_marriage_course']
            
            # Process bride information
            application.bride_fullname = request.POST.get('bride_fullname')
            application.bride_id_number = request.POST.get('bride_id_number')
            application.bride_dob = request.POST.get('bride_dob')
            application.bride_nationality = request.POST.get('bride_nationality')
            application.bride_religion = request.POST.get('bride_religion')
            application.bride_marital_status = request.POST.get('bride_marital_status')
            application.bride_address = request.POST.get('bride_address')
            
            # Process wali information
            application.wali_name = request.POST.get('wali_name')
            application.wali_ic = request.POST.get('wali_ic')
            
            # Process bride and wali documents
            if 'bride_ic_copy' in request.FILES:
                application.bride_ic_copy = request.FILES['bride_ic_copy']
            if 'bride_hiv_test' in request.FILES:
                application.bride_hiv_test = request.FILES['bride_hiv_test']
            if 'bride_marriage_course' in request.FILES:
                application.bride_marriage_course = request.FILES['bride_marriage_course']
            if 'wali_ic_copy' in request.FILES:
                application.wali_ic_copy = request.FILES['wali_ic_copy']
            if 'wali_consent' in request.FILES:
                application.wali_consent = request.FILES['wali_consent']
            
            # Save the application
            application.save()
            
            messages.success(request, 'Marriage application submitted successfully!')
            return redirect('track_application')  # Replace with your success URL
            
        except Exception as e:
            messages.error(request, f'Error submitting application: {str(e)}')
            return redirect('submit_application')  # Redirect back to form
    
    # For GET requests, show the form
    context = {
        'form_id': uuid.uuid4(),  # Generate a new form ID for each form load
        'username': user.username,  # Display username in template
        'user_id_number': user.id_number  # Display user's ID number if needed
    }
    return render(request, 'submitapplicationpage.html', context)


def track_application(request):
    if not request.session.get('user_id'):
        messages.error(request, 'You need to login to view applications')
        return redirect('login')

    try:
        user = User.objects.get(id=request.session['user_id'])
        applications = BrideGroomApplication.objects.filter(user=user).select_related('user').order_by('-created_at')
        
        context = {
            'username': user.username,
            'fullname': user.fullname,  # From your User model
            'applications': applications,
            'user_id_number': user.id_number  # If you want to display this
        }
        return render(request, 'trackapplicationpage.html', context)
        
    except User.DoesNotExist:
        messages.error(request, 'User not found')
        return redirect('login')
    except Exception as e:
        messages.error(request, f'Error loading applications: {str(e)}')
        return redirect('bridegroom_account')
    

from django.core.paginator import Paginator

def pending_application(request):
    if not request.session.get('user_id') or request.session.get('user_role') != 'imam':
        return redirect('signin')
    
    # Get filter parameters from request
    status_filter = request.GET.get('status', '').lower()
    search_query = request.GET.get('search', '')

    # Start with base queryset
    applications = BrideGroomApplication.objects.all().order_by('-created_at')

    # Apply status filter if specified
    if status_filter in ['pending', 'approved', 'rejected']:
        applications = applications.filter(status__iexact=status_filter)

    # Apply search filter if specified
    if search_query:
        applications = applications.filter(
            Q(groom_fullname__icontains=search_query) |
            Q(bride_fullname__icontains=search_query) |
            Q(application_id__icontains=search_query) |
            Q(user__username__icontains=search_query)
        )

    # Paginate results (10 per page)
    paginator = Paginator(applications, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'applications': page_obj,
        'status_filter': status_filter,
        'search_query': search_query,
    }

    return render(request, 'pendingapplication.html', context)

def view_application(request, application_id):
    if not request.session.get('user_id') or request.session.get('user_role') != 'imam':
        return redirect('signin')

    try:
        application = BrideGroomApplication.objects.get(application_id=application_id)
        context = {
            'application': application,
            'documents': {
                'groom_ic': bool(application.groom_ic_copy),
                'bride_ic': bool(application.bride_ic_copy),
                'groom_hiv': bool(application.groom_hiv_test),
                'bride_hiv': bool(application.bride_hiv_test),
                'groom_course': bool(application.groom_marriage_course),
                'bride_course': bool(application.bride_marriage_course),
                'wali_ic': bool(application.wali_ic_copy),
                'wali_consent': bool(application.wali_consent),
            }
        }
        return render(request, 'viewapplication.html', context)

    except BrideGroomApplication.DoesNotExist:
        messages.error(request, 'Application not found')
        return redirect('pending_application')

def approve_application(request, application_id):
    if not request.session.get('user_id') or request.session.get('user_role') != 'imam':
        return redirect('signin')

    try:
        application = BrideGroomApplication.objects.get(application_id=application_id)
        if application.status != 'PENDING':
            messages.warning(request, 'This application has already been processed.')
        else:
            application.status = 'APPROVED'
            application.processed_by = request.user
            application.save()
            messages.success(request, 'Application approved successfully.')
        return redirect('pending_application')

    except BrideGroomApplication.DoesNotExist:
        messages.error(request, 'Application not found')
        return redirect('pending_application')

def reject_application(request, application_id):
    if not request.session.get('user_id') or request.session.get('user_role') != 'imam':
        return redirect('signin')

    if request.method == 'POST':
        try:
            application = BrideGroomApplication.objects.get(application_id=application_id)
            if application.status != 'PENDING':
                messages.warning(request, 'This application has already been processed.')
            else:
                application.status = 'REJECTED'
                application.remarks = request.POST.get('remarks', 'No remarks provided.')
                application.processed_by = request.user
                application.save()
                messages.success(request, 'Application rejected.')
            return redirect('pending_application')

        except BrideGroomApplication.DoesNotExist:
            messages.error(request, 'Application not found')
            return redirect('pending_application')
    else:
        return redirect('pending_application')
    
def generate_calendar_days(year, month, availability_model, filter_kwargs):
    cal = calendar.monthcalendar(year, month)
    first_day = datetime(year, month, 1).date()
    last_day = datetime(year, month, calendar.monthrange(year, month)[1]).date()
    
    # Get availability from the model
    availabilities = availability_model.objects.filter(
        date__gte=first_day,
        date__lte=last_day,
        **filter_kwargs
    ).order_by('date')
    
    availability_dict = {avail.date: avail for avail in availabilities}
    
    calendar_days = []
    today = timezone.now().date()
    
    for week in cal:
        week_days = []
        for day in week:
            if day == 0:
                week_days.append({'day': None, 'status': None})
                continue

            date = datetime(year, month, day).date()
            status = None
            css_class = ''
            
            if date < today:
                css_class = 'day-past'
                
            if date in availability_dict:
                avail = availability_dict[date]
                status = avail.status
                # Combine classes if it's a past date with status
                css_class = f'{css_class} day-{status}'.strip()
            
            week_days.append({
                'day': day,
                'date': date.isoformat(),  # This will be in 'YYYY-MM-DD' format
                'status': status,
                'css_class': css_class,
                'is_available': status == 'available'  # Add explicit availability flag
            })
        calendar_days.append(week_days)
    
    return calendar_days

def imam_scheduleimam(request):
    if not request.session.get('user_id'):
        messages.error(request, 'You need to login to submit an application')
        return redirect('signin')
    
    user = User.objects.get(id=request.session['user_id'])
    
    # Handle form submission
    if request.method == 'POST':
        try:
            date_str = request.POST.get('date')
            status = request.POST.get('status')
            time_slots = request.POST.getlist('time_slots')  # Note: changed from time_slots[]
            notes = request.POST.get('notes', '')
            
            if not date_str:
                raise ValueError("Date is required")
                
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            # Create or update availability
            ImamAvailability.objects.update_or_create(
                imam=user,
                date=date,
                defaults={
                    'status': status,
                    'time_slots': time_slots,
                    'notes': notes
                }
            )
            messages.success(request, 'Availability updated successfully!')
            
            # Redirect to the same month view
            return redirect(f"{request.path}?month={date.month}&year={date.year}")
            
        except Exception as e:
            messages.error(request, f'Error updating availability: {str(e)}')
            # On error, fall through to render the page with error message
    # Get current month/year or from query
    now = timezone.now()
    current_month = now.month
    current_year = now.year

    month = int(request.GET.get('month', current_month))
    year = int(request.GET.get('year', current_year))
    calendar_days = generate_calendar_days(year, month, ImamAvailability, {'imam': user})
    
    # Define time slots for the template
    time_slot_choices = [
        ('morning', 'Morning \n (8 AM - 12 PM)'),
        ('afternoon', 'Afternoon \n (12 PM - 7 PM)'),
        ('evening', 'Evening \n (7 PM - 10 PM)'),
    ]
    
    selected_date_details = None
    if request.GET.get('selected_date'):
        try:
            selected_date = datetime.strptime(request.GET.get('selected_date'), '%Y-%m-%d').date()
            selected_date_details = ImamAvailability.objects.filter(
                imam=user,
                date=selected_date
            ).first()
        except:
            pass

    context = {
        'user': user,
        'calendar_days': calendar_days,
        'month_name':  calendar.month_name[month],
        'year': year,
        'month': month,
        'prev_month': month - 1 if month > 1 else 12,
        'prev_year': year if month > 1 else year - 1,
        'next_month': month + 1 if month < 12 else 1,
        'next_year': year if month < 12 else year + 1,
        'weekdays': ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
        'time_slots': time_slot_choices,
        'selected_date': request.POST.get('date', ''),
        'selected_status': request.POST.get('status', ''),
        'selected_time_slots': request.POST.getlist('time_slots', []),
        'selected_notes': request.POST.get('notes', ''),
        'selected_date_details': selected_date_details,
    }
    
    return render(request, 'imamschedulepage-imam.html', context)


def solemnisation_management(request):
    if not request.session.get('user_id'):
        messages.error(request, 'You need to signin to submit an application')
        return redirect('signin')
    
    user = User.objects.get(id=request.session['user_id'])
    
    # Handle form submission
    if request.method == 'POST':
        try:
            # Get multiple dates from comma-separated string
            dates_str = request.POST.get('selected_dates', '')
            status = request.POST.get('status')
            time_slots = request.POST.getlist('time_slots') 
            notes = request.POST.get('notes', '')
            
            if not dates_str:
                raise ValueError("At least one date is required")
                
            # Split and process multiple dates
            date_strings = [d.strip() for d in dates_str.split(',') if d.strip()]
            
            for date_str in date_strings:
                date = datetime.strptime(date_str, '%Y-%m-%d').date()
                
                # Create or update SolemnisationSlot for each date
                SolemnisationSlot.objects.update_or_create(
                    date=date,
                    defaults={
                        'status': status,
                        'time_slots': time_slots,
                        'notes': notes
                    }
                )
            
            messages.success(request, f'Successfully updated {len(date_strings)} date(s)!')
            
            # Redirect to the same month view
            return redirect(f"{request.path}?month={date.month}&year={date.year}")
            
        except Exception as e:
            messages.error(request, f'Error updating availability: {str(e)}')
    
    # Rest of your existing calendar generation code remains the same
    # Get current month and year (for both GET and failed POST cases)
    now = timezone.now()
    current_month = now.month
    current_year = now.year
    
    # Get requested month/year from query params
    month = int(request.GET.get('month', current_month))
    year = int(request.GET.get('year', current_year))
    
    calendar_days = generate_calendar_days(year, month, SolemnisationSlot, {})
    
    # Define time slots for the template
    time_slot_choices = [
        ('morning', 'Morning \n (8 AM - 12 PM)'),
        ('afternoon', 'Afternoon \n (12 PM - 7 PM)'),
        ('evening', 'Evening \n (7 PM - 10 PM)'),
    ]
    
    selected_date_details = None
    if request.GET.get('selected_date'):
        try:
            selected_date = datetime.strptime(request.GET.get('selected_date'), '%Y-%m-%d').date()
            selected_date_details = SolemnisationSlot.objects.filter(
                date=selected_date
            ).first()
        except:
            pass

    context = {
        'user': user,
        'calendar_days': calendar_days,
        'month_name': calendar.month_name[month],
        'year': year,
        'month': month,
        'prev_month': month - 1 if month > 1 else 12,
        'prev_year': year if month > 1 else year - 1,
        'next_month': month + 1 if month < 12 else 1,
        'next_year': year if month < 12 else year + 1,
        'weekdays': ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
        'time_slots': time_slot_choices,
        'selected_dates': request.POST.get('selected_dates', ''),
        'selected_status': request.POST.get('status', ''),
        'selected_time_slots': request.POST.getlist('time_slots', []),
        'selected_notes': request.POST.get('notes', ''),
        'selected_date_details': selected_date_details,
    }
    
    return render(request, 'managesolemnisationsch-page.html', context)
    
def submit_booking(request):
    if not request.session.get('user_id'):
        messages.error(request, 'You need to signin to submit an application')
        return redirect('signin')

    try:
        user = User.objects.get(id=request.session['user_id'])
    except User.DoesNotExist:
        messages.error(request, 'User not found')
        return redirect('signin')
    
    try:
        application = BrideGroomApplication.objects.filter(user=user).latest('created_at')
        groom_name = application.groom_fullname
        bride_name = application.bride_fullname
    except BrideGroomApplication.DoesNotExist:
        groom_name = ''
        bride_name = ''

    # Define time slot display labels (used in calendar & form)
    TIME_SLOT_CHOICES = [
        ('morning', 'Morning (8AM-12PM)'),
        ('afternoon', 'Afternoon (12PM-7PM)'),
        ('evening', 'Evening (7PM-10PM)'),
    ]
    
    # Define time slot ranges with sub-ranges
    TIME_SLOT_RANGES = {
        'morning': ['8-9', '9-10', '10-11', '11-12'],
        'afternoon': ['12-1', '1-2', '2-3', '3-4', '4-5', '5-6', '6-7'],
        'evening': ['7-8', '8-9', '9-10']
    }

    # Get current or requested month/year
    now = timezone.now()
    current_month = now.month
    current_year = now.year

    month = int(request.GET.get('month', current_month))
    year = int(request.GET.get('year', current_year))

    selected_date = request.GET.get('selected_date')

    # Generate calendar view
    calendar_days = generate_calendar_days(year, month, SolemnisationSlot, {})

    # If POST request: handle form submission
    if request.method == 'POST':
        try:
            # Extract form data
            groom_name = request.POST.get('groom_name')
            bride_name = request.POST.get('bride_name')
            booking_date_str = request.POST.get('booking_date')
            specific_time_str = request.POST.get('specific_time')  # e.g., "9-10"
            selected_slot = request.POST.get('selected_slot')      # e.g., "morning"
            location = request.POST.get('location')
            notes = request.POST.get('notes', '')

            if not all([booking_date_str, selected_slot, specific_time_str, location]):
                raise ValueError("All required fields must be filled")

            # Convert sub-range to specific time (take the start hour)
            try:
                start_str, end_str = specific_time_str.split('-')
                start_hour = int(start_str)
                end_hour = int(end_str)

                # Adjust based on time slot
                if selected_slot == 'afternoon':
                    start_hour += 12 if start_hour < 12 else 0
                    end_hour += 12 if end_hour < 12 else 0
                elif selected_slot == 'evening':
                    start_hour += 12 if start_hour < 12 else 0
                    end_hour += 12 if end_hour < 12 else 0
                # Morning times are already correct

                start_time = time(start_hour, 0)
                end_time = time(end_hour, 0)

            except (ValueError, IndexError):
                raise ValueError("Invalid time format")

            # Convert booking date
            booking_date = datetime.strptime(booking_date_str, '%Y-%m-%d').date()

            # Create and save booking
            booking = SolemnisationBooking(
                groom_name=groom_name,
                bride_name=bride_name,
                user=user,
                booking_id=uuid.uuid4(),
                booking_date=booking_date,
                time_slot=selected_slot,
                start_time=start_time,
                end_time=end_time,
                location=location,
                notes=notes,
                status='PENDING'
            )
            booking.save()

            messages.success(request, 'Marriage booking submitted successfully!')
            return redirect('track_booking')

        except Exception as e:
            messages.error(request, f'Error submitting booking: {str(e)}')
            return redirect('book_solemnisation')

    # For GET: load selected date's availability
    selected_date_details = None
    if selected_date:
        try:
            date_obj = datetime.strptime(selected_date, '%Y-%m-%d').date()
            availability = SolemnisationSlot.objects.get(date=date_obj)
            
            # Get all bookings for this date to determine taken sub-ranges
            existing_bookings = SolemnisationBooking.objects.filter(
                booking_date=date_obj,
                status__in=['PENDING', 'APPROVED']
            )
            
            # Create a dict of taken sub-ranges per slot
            taken_sub_ranges = {
                'morning': [],
                'afternoon': [],
                'evening': []  # This should match your model's time_slot choices
            }
            
            for booking in existing_bookings:
                start_hour = booking.start_time.hour
                end_hour = booking.end_time.hour
                sub_range = f"{start_hour}-{end_hour}"
                
                if booking.time_slot in taken_sub_ranges:
                    taken_sub_ranges[booking.time_slot].append(sub_range)

            
            selected_date_details = {
                'status': availability.status,
                'time_slots': availability.time_slots or [],
                'notes': availability.notes,
                'taken_sub_ranges': taken_sub_ranges,
                'time_slot_ranges': TIME_SLOT_RANGES,
                # Add pre-processed data
                'morning_ranges': TIME_SLOT_RANGES.get('morning', []),
                'afternoon_ranges': TIME_SLOT_RANGES.get('afternoon', []),
                'evening_ranges': TIME_SLOT_RANGES.get('evening', []),
                'morning_taken': taken_sub_ranges.get('morning', []),
                'afternoon_taken': taken_sub_ranges.get('afternoon', []),
                'evening_taken': taken_sub_ranges.get('evening', []),
            }
        except SolemnisationSlot.DoesNotExist:
            pass

    context = {
        'calendar_days': calendar_days,
        'month_name': calendar.month_name[month],
        'year': year,
        'month': month,
        'prev_month': month - 1 if month > 1 else 12,
        'prev_year': year if month > 1 else year - 1,
        'next_month': month + 1 if month < 12 else 1,
        'next_year': year if month < 12 else year + 1,
        'weekdays': ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
        'selected_date': selected_date,
        'time_slots': TIME_SLOT_CHOICES,
        'selected_date_details': selected_date_details,
        'username': user.username,
        'form_id': uuid.uuid4(),
        'groom_name': groom_name,
        'bride_name': bride_name,
    }

    return render(request, 'submitbookingpage.html', context)

def track_booking(request):
    if not request.session.get('user_id'):
        messages.error(request, 'You need to signin to view bookings')
        return redirect('signin')

    try:
        user = User.objects.get(id=request.session['user_id'])
        bookings = SolemnisationBooking.objects.filter(user=user).select_related('user').order_by('-created_at')
        
        context = {
            'username': user.username,
            'fullname': user.fullname,  # From your User model
            'bookings': bookings,
            'user_id_number': user.id_number  # If you want to display this
        }
        return render(request, 'trackbookingpage.html', context)
        
    except User.DoesNotExist:
        messages.error(request, 'User not found')
        return redirect('signin')
    except Exception as e:
        messages.error(request, f'Error loading bookings: {str(e)}')
        return redirect('bridegroom_account')
    
    
def manage_applications(request):
    """Admin view for managing marriage applications (create/edit/delete)"""
    if not request.session.get('user_id') or request.session.get('user_role') != 'adminchairman':
        return redirect('signin')
    
    # Get filter parameters from request
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('search', '')

    # Start with base queryset
    applications = BrideGroomApplication.objects.all().order_by('-created_at')

    # Apply status filter if specified
    if status_filter:
        applications = applications.filter(status__iexact=status_filter)

    # Apply search filter if specified
    if search_query:
        applications = applications.filter(
            Q(groom_fullname__icontains=search_query) |
            Q(bride_fullname__icontains=search_query) |
            Q(application_id__icontains=search_query) |
            Q(user__username__icontains=search_query)
        )

    # Paginate results (10 per page)
    paginator = Paginator(applications, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'applications': page_obj,
        'status_filter': status_filter,
        'search_query': search_query,
    }

    return render(request, 'manageapplication.html', context)

def create_application(request):
    # Check authentication
    if not request.session.get('user_id'):
        messages.error(request, 'You need to login to submit an application')
        return redirect('signin')
    
    try:
        user = User.objects.get(id=request.session['user_id'])
    except User.DoesNotExist:
        messages.error(request, 'User not found')
        return redirect('signin')

    if request.method == 'POST':
        try:
            # Create new application instance
            application = BrideGroomApplication()
            
            # Set basic application info
            application.user = user
            application.application_id = uuid.uuid4()
            application.status = 'PENDING'
            
            # Process groom information
            application.groom_fullname = request.POST.get('groom_fullname', '').strip()
            application.groom_id_number = request.POST.get('groom_id_number', '').strip()
            application.groom_dob = request.POST.get('groom_dob')
            application.groom_nationality = request.POST.get('groom_nationality', '').strip()
            application.groom_religion = request.POST.get('groom_religion', '').strip()
            application.groom_marital_status = request.POST.get('groom_marital_status')
            application.groom_address = request.POST.get('groom_address', '').strip()
            
            # Process groom documents
            if 'groom_ic_copy' in request.FILES:
                application.groom_ic_copy = request.FILES['groom_ic_copy']
            if 'groom_hiv_test' in request.FILES:
                application.groom_hiv_test = request.FILES['groom_hiv_test']
            if 'groom_marriage_course' in request.FILES:
                application.groom_marriage_course = request.FILES['groom_marriage_course']
            
            # Process bride information
            application.bride_fullname = request.POST.get('bride_fullname', '').strip()
            application.bride_id_number = request.POST.get('bride_id_number', '').strip()
            application.bride_dob = request.POST.get('bride_dob')
            application.bride_nationality = request.POST.get('bride_nationality', '').strip()
            application.bride_religion = request.POST.get('bride_religion', '').strip()
            application.bride_marital_status = request.POST.get('bride_marital_status')
            application.bride_address = request.POST.get('bride_address', '').strip()
            
            # Process wali information
            application.wali_name = request.POST.get('wali_name', '').strip()
            application.wali_ic = request.POST.get('wali_ic', '').strip()
            
            # Process bride and wali documents
            if 'bride_ic_copy' in request.FILES:
                application.bride_ic_copy = request.FILES['bride_ic_copy']
            if 'bride_hiv_test' in request.FILES:
                application.bride_hiv_test = request.FILES['bride_hiv_test']
            if 'bride_marriage_course' in request.FILES:
                application.bride_marriage_course = request.FILES['bride_marriage_course']
            if 'wali_ic_copy' in request.FILES:
                application.wali_ic_copy = request.FILES['wali_ic_copy']
            if 'wali_consent' in request.FILES:
                application.wali_consent = request.FILES['wali_consent']
            
            # Save the application
            application.save()
            
            messages.success(request, 'Marriage application submitted successfully!')
            
            # Redirect based on user role
            if request.session.get('user_role') == 'adminchairman':
                return redirect('application_management')
            
        except Exception as e:
            messages.error(request, f'Error submitting application: {str(e)}')
            return redirect(request.path)  # Redirect back to the same page

    # For GET requests, show the form
    context = {
        'form_id': uuid.uuid4(),  # Generate a new form ID for each form load
    }
    
    # Use different templates based on user role
    if request.session.get('user_role') == 'adminchairman':
        return render(request, 'createapplicationpage.html', context)
    else:
        return render(request, 'submitapplicationpage.html', context)
    

def manage_bookings(request):
    if not request.session.get('user_id') or request.session.get('user_role') != 'adminchairman':
        return redirect('signin')
    

    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('search', '')

    bookings = SolemnisationBooking.objects.all().select_related('user').order_by('-updated_at')
    
    if status_filter:
        bookings = bookings.filter(status=status_filter)
    
    if search_query:
        bookings = bookings.filter(
            Q(booking_id__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(location__icontains=search_query)
        )

    context = {
        'bookings': bookings,
        'status_filter': status_filter,
        'search_query': search_query,
    }
    return render(request, 'managebooking.html', context)


def create_booking(request):
    if request.session.get('user_role') != 'adminchairman':
        messages.error(request, 'You need to signin as admin to create a booking')
        return redirect('signin')

    try:
        user = User.objects.get(id=request.session['user_id'])
    except User.DoesNotExist:
        messages.error(request, 'User not found')
        return redirect('signin')
    try:
        application = BrideGroomApplication.objects.filter(user=user).latest('created_at')
        groom_name = application.groom_fullname
        bride_name = application.bride_fullname
    except BrideGroomApplication.DoesNotExist:
        groom_name = ''
        bride_name = ''

    # Define time slot display labels (used in calendar & form)
    TIME_SLOT_CHOICES = [
        ('morning', 'Morning (8AM-12PM)'),
        ('afternoon', 'Afternoon (12PM-7PM)'),
        ('evening', 'Evening (7PM-10PM)'),
    ]
    # Define time slot ranges with sub-ranges
    TIME_SLOT_RANGES = {
        'morning': ['8-9', '9-10', '10-11', '11-12'],
        'afternoon': ['12-1', '1-2', '2-3', '3-4', '4-5', '5-6', '6-7'],
        'evening': ['7-8', '8-9', '9-10']
    }

    # Get current or requested month/year
    now = timezone.now()
    current_month = now.month
    current_year = now.year

    month = int(request.GET.get('month', current_month))
    year = int(request.GET.get('year', current_year))

    selected_date = request.GET.get('selected_date')

    # Generate calendar view
    calendar_days = generate_calendar_days(year, month, SolemnisationSlot, {})

    # If POST request: handle form submission
    if request.method == 'POST':
        try:
            # Extract form data
            groom_name = request.POST.get('groom_name')
            bride_name = request.POST.get('bride_name')
            booking_date_str = request.POST.get('booking_date')
            selected_slot = request.POST.get('selected_slot')  # e.g., 'morning'
            specific_time_str = request.POST.get('specific_time')
            location = request.POST.get('location')
            notes = request.POST.get('notes', '')

            if not booking_date_str or not selected_slot or not specific_time_str or not location:
                raise ValueError("All fields are required")

            # Convert sub-range to specific time (take the start hour)
            try:
                start_str, end_str = specific_time_str.split('-')
                start_hour = int(start_str)
                end_hour = int(end_str)

                # Adjust based on time slot
                if selected_slot == 'afternoon':
                    start_hour += 12 if start_hour < 12 else 0
                    end_hour += 12 if end_hour < 12 else 0
                elif selected_slot == 'evening':
                    start_hour += 12 if start_hour < 12 else 0
                    end_hour += 12 if end_hour < 12 else 0
                # Morning times are already correct

                start_time = time(start_hour, 0)
                end_time = time(end_hour, 0)

            except (ValueError, IndexError):
                raise ValueError("Invalid time format")
            
            # Convert types
            booking_date = datetime.strptime(booking_date_str, '%Y-%m-%d').date()
            # Create and save booking
            booking = SolemnisationBooking(
                groom_name=groom_name,
                bride_name=bride_name,
                user=user,
                booking_id=uuid.uuid4(),
                booking_date=booking_date,
                time_slot=selected_slot,
                start_time=start_time,
                end_time=end_time,
                location=location,
                notes=notes,
                status='PENDING'
            )
            booking.save()

            messages.success(request, 'Marriage booking submitted successfully!')
            return redirect('booking_management')  # Update with your tracking page route

        except Exception as e:
            messages.error(request, f'Error submitting booking: {str(e)}')
            return redirect('create_booking')  # Redirect back to the form

    # For GET: load selected date's availability
    selected_date_details = None
    if selected_date:
        try:
            date_obj = datetime.strptime(selected_date, '%Y-%m-%d').date()
            availability = SolemnisationSlot.objects.get(date=date_obj)
            
            # Get all bookings for this date to determine taken sub-ranges
            existing_bookings = SolemnisationBooking.objects.filter(
                booking_date=date_obj,
                status__in=['PENDING', 'APPROVED']
            )
            
            # Create a dict of taken sub-ranges per slot
            taken_sub_ranges = {
                'morning': [],
                'afternoon': [],
                'evening': []  # This should match your model's time_slot choices
            }
            
            for booking in existing_bookings:
                start_hour = booking.start_time.hour
                end_hour = booking.end_time.hour
                sub_range = f"{start_hour}-{end_hour}"
                
                if booking.time_slot in taken_sub_ranges:
                    taken_sub_ranges[booking.time_slot].append(sub_range)

            
            selected_date_details = {
                'status': availability.status,
                'time_slots': availability.time_slots or [],
                'notes': availability.notes,
                'taken_sub_ranges': taken_sub_ranges,
                'time_slot_ranges': TIME_SLOT_RANGES,
                # Add pre-processed data
                'morning_ranges': TIME_SLOT_RANGES.get('morning', []),
                'afternoon_ranges': TIME_SLOT_RANGES.get('afternoon', []),
                'evening_ranges': TIME_SLOT_RANGES.get('evening', []),
                'morning_taken': taken_sub_ranges.get('morning', []),
                'afternoon_taken': taken_sub_ranges.get('afternoon', []),
                'evening_taken': taken_sub_ranges.get('evening', []),
            }
        except SolemnisationSlot.DoesNotExist:
            pass

    context = {
        'calendar_days': calendar_days,
        'month_name': calendar.month_name[month],
        'year': year,
        'month': month,
        'prev_month': month - 1 if month > 1 else 12,
        'prev_year': year if month > 1 else year - 1,
        'next_month': month + 1 if month < 12 else 1,
        'next_year': year if month < 12 else year + 1,
        'weekdays': ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
        'selected_date': selected_date,
        'time_slots': TIME_SLOT_CHOICES,
        'selected_date_details': selected_date_details,
        'username': user.username,
        'form_id': uuid.uuid4(),
        'groom_name': groom_name,
        'bride_name': bride_name,
    }

    return render(request, 'createbooking.html', context)

def view_booking(request,booking_id):
    if request.session.get('user_role') != 'adminchairman':
        return redirect('signin')
    try:
        booking = SolemnisationBooking.objects.get(booking_id=booking_id)
        
        context = {
            'booking': booking,
        }
        return render(request, 'viewbooking.html', context)
        
    except Exception as e:
        messages.error(request, f'Error loading bookings: {str(e)}')
        return redirect('booking_management')
    


    except BrideGroomApplication.DoesNotExist:
        messages.error(request, 'Application not found')
        return redirect('pending_application')
    
def approve_booking(request, booking_id):
    if request.session.get('user_role') != 'adminchairman':
        return redirect('signin')

    try:
        booking = SolemnisationBooking.objects.get(booking_id=booking_id)
        if booking.status != 'PENDING':
            messages.warning(request, 'This booking has already been processed')
        else:
            booking.status = 'APPROVED'
            booking.processed_by = request.user
            booking.save()
            messages.success(request, 'Booking approved successfully')
        return redirect('booking_management')

    except SolemnisationBooking.DoesNotExist:
        messages.error(request, 'Booking not found')
        return redirect('booking_management')

def reject_booking(request, booking_id):
    if request.session.get('user_role') != 'adminchairman':
        return redirect('signin')

    if request.method == 'POST':
        try:
            booking = SolemnisationBooking.objects.get(booking_id=booking_id)
            if booking.status != 'PENDING':
                messages.warning(request, 'This booking has already been processed')
            else:
                booking.status = 'REJECTED'
                booking.remarks = request.POST.get('remarks', 'No remarks provided')
                booking.processed_by = request.user
                booking.save()
                messages.success(request, 'Booking is rejected')
            return redirect('booking_management')

        except SolemnisationBooking.DoesNotExist:
            messages.error(request, 'Booking not found')
            return redirect('booking_management')
    else:
        return redirect('booking_management')
    

def edit_application(request, application_id):
    if request.session.get('user_role') != 'adminchairman':
        return redirect('signin')

    try:
        # Fetch the existing application to edit (not create a new one!)
        application = BrideGroomApplication.objects.get(
            application_id=application_id,
        )
    except BrideGroomApplication.DoesNotExist:
        messages.error(request, 'Application not found or access denied')
        return redirect('application_management')  # Redirect to a safe page

    if request.method == 'POST':
        try:
            # === Update fields (do NOT create a new application) ===
            # Process groom information
            application.groom_fullname = request.POST.get('groom_fullname', '').strip()
            application.groom_id_number = request.POST.get('groom_id_number', '').strip()
            application.groom_dob = request.POST.get('groom_dob')
            application.groom_nationality = request.POST.get('groom_nationality', '').strip()
            application.groom_religion = request.POST.get('groom_religion', '').strip()
            application.groom_marital_status = request.POST.get('groom_marital_status')
            application.groom_address = request.POST.get('groom_address', '').strip()
            
            # Process groom documents (only update if new files are provided)
            if 'groom_ic_copy' in request.FILES:
                application.groom_ic_copy = request.FILES['groom_ic_copy']
            if 'groom_hiv_test' in request.FILES:
                application.groom_hiv_test = request.FILES['groom_hiv_test']
            if 'groom_marriage_course' in request.FILES:
                application.groom_marriage_course = request.FILES['groom_marriage_course']
            
            # Process bride information
            application.bride_fullname = request.POST.get('bride_fullname', '').strip()
            application.bride_id_number = request.POST.get('bride_id_number', '').strip()
            application.bride_dob = request.POST.get('bride_dob')
            application.bride_nationality = request.POST.get('bride_nationality', '').strip()
            application.bride_religion = request.POST.get('bride_religion', '').strip()
            application.bride_marital_status = request.POST.get('bride_marital_status')
            application.bride_address = request.POST.get('bride_address', '').strip()
            
            # Process wali information
            application.wali_name = request.POST.get('wali_name', '').strip()
            application.wali_ic = request.POST.get('wali_ic', '').strip()
            
            # Process bride and wali documents
            if 'bride_ic_copy' in request.FILES:
                application.bride_ic_copy = request.FILES['bride_ic_copy']
            if 'bride_hiv_test' in request.FILES:
                application.bride_hiv_test = request.FILES['bride_hiv_test']
            if 'bride_marriage_course' in request.FILES:
                application.bride_marriage_course = request.FILES['bride_marriage_course']
            if 'wali_ic_copy' in request.FILES:
                application.wali_ic_copy = request.FILES['wali_ic_copy']
            if 'wali_consent' in request.FILES:
                application.wali_consent = request.FILES['wali_consent']
            
            # Save updates (no new application_id needed)
            application.save()
            
            messages.success(request, 'Application updated successfully!')
            return redirect('application_management')  # Redirect after success

        except Exception as e:
            messages.error(request, f'Error updating application: {str(e)}')
            return redirect(request.path)

    # For GET requests, pre-fill the form with existing data
    context = {
        'application': application,  # Pass the existing application to the template
    }
    return render(request, 'editapplication.html', context)

def delete_application(request, application_id):
    # Check authentication and admin role
    if not request.session.get('user_id') or request.session.get('user_role') != 'adminchairman':
        messages.error(request, 'You need admin privileges to perform this action')
        return redirect('signin')
    
    try:
        # Get the application to delete
        application = BrideGroomApplication.objects.get(application_id=application_id)
        
        # Delete the application
        application.delete()
        messages.success(request, 'Application deleted successfully!')
        
    except BrideGroomApplication.DoesNotExist:
        messages.error(request, 'Application not found')
    except Exception as e:
        messages.error(request, f'Error deleting application: {str(e)}')
    
    return redirect('application_management')

def edit_booking(request, booking_id):
    if request.session.get('user_role') != 'adminchairman':
        messages.error(request, 'You need to signin as admin to edit a booking')
        return redirect('signin')

    try:
        user = User.objects.get(id=request.session['user_id'])
    except User.DoesNotExist:
        messages.error(request, 'User not found')
        return redirect('signin')

    try:
        booking = SolemnisationBooking.objects.get(booking_id=booking_id)
    except SolemnisationBooking.DoesNotExist:
        messages.error(request, 'Booking not found')
        return redirect('booking_management')

    # Define time slot display labels (used in calendar & form)
    TIME_SLOT_CHOICES = [
        ('morning', 'Morning (8AM-12PM)'),
        ('afternoon', 'Afternoon (12PM-7PM)'),
        ('evening', 'Evening (7PM-10PM)'),
    ]
    # Define time slot ranges with sub-ranges
    TIME_SLOT_RANGES = {
        'morning': ['8-9', '9-10', '10-11', '11-12'],
        'afternoon': ['12-1', '1-2', '2-3', '3-4', '4-5', '5-6', '6-7'],
        'evening': ['7-8', '8-9', '9-10']
    }

    # Get current or requested month/year
    now = timezone.now()
    current_month = now.month
    current_year = now.year

    month = int(request.GET.get('month', booking.booking_date.month))
    year = int(request.GET.get('year', booking.booking_date.year))

    selected_date = request.GET.get('selected_date', booking.booking_date.strftime('%Y-%m-%d'))

    # Generate calendar view
    calendar_days = generate_calendar_days(year, month, SolemnisationSlot, {})

    # If POST request: handle form submission
    if request.method == 'POST':
        try:
            # Extract form data
            groom_name = request.POST.get('groom_name')
            bride_name = request.POST.get('bride_name')
            booking_date_str = request.POST.get('booking_date')
            selected_slot = request.POST.get('selected_slot')  # e.g., 'morning'
            specific_time_str = request.POST.get('specific_time')
            location = request.POST.get('location')
            notes = request.POST.get('notes', '')

            if not booking_date_str or not selected_slot or not specific_time_str or not location:
                raise ValueError("All fields are required")

            # Convert sub-range to specific time (take the start hour)
            try:
                start_str, end_str = specific_time_str.split('-')
                start_hour = int(start_str)
                end_hour = int(end_str)

                # Adjust based on time slot
                if selected_slot == 'afternoon':
                    start_hour += 12 if start_hour < 12 else 0
                    end_hour += 12 if end_hour < 12 else 0
                elif selected_slot == 'evening':
                    start_hour += 12 if start_hour < 12 else 0
                    end_hour += 12 if end_hour < 12 else 0
                # Morning times are already correct

                start_time = time(start_hour, 0)
                end_time = time(end_hour, 0)

            except (ValueError, IndexError):
                raise ValueError("Invalid time format")
            
            # Convert types
            booking_date = datetime.strptime(booking_date_str, '%Y-%m-%d').date()
            
            # Update booking
            booking.groom_name = groom_name
            booking.bride_name = bride_name
            booking.booking_date = booking_date
            booking.time_slot = selected_slot
            booking.start_time = start_time
            booking.end_time = end_time
            booking.location = location
            booking.notes = notes
            booking.status = 'PENDING'  # Reset status to pending for admin review
            booking.save()

            messages.success(request, 'Booking updated successfully!')
            return redirect('booking_management')

        except Exception as e:
            messages.error(request, f'Error updating booking: {str(e)}')
            return redirect('edit_booking', booking_id=booking_id)

    # For GET: load selected date's availability
    selected_date_details = None
    if selected_date:
        try:
            date_obj = datetime.strptime(selected_date, '%Y-%m-%d').date()
            availability = SolemnisationSlot.objects.get(date=date_obj)
            
            # Get all bookings for this date to determine taken sub-ranges (excluding current booking)
            existing_bookings = SolemnisationBooking.objects.filter(
                booking_date=date_obj,
                status__in=['PENDING', 'APPROVED']
            ).exclude(booking_id=booking_id)
            
            # Create a dict of taken sub-ranges per slot
            taken_sub_ranges = {
                'morning': [],
                'afternoon': [],
                'evening': []  # This should match your model's time_slot choices
            }
            
            for booking in existing_bookings:
                start_hour = booking.start_time.hour
                end_hour = booking.end_time.hour
                sub_range = f"{start_hour}-{end_hour}"
                
                if booking.time_slot in taken_sub_ranges:
                    taken_sub_ranges[booking.time_slot].append(sub_range)

            selected_date_details = {
                'status': availability.status,
                'time_slots': availability.time_slots or [],
                'notes': availability.notes,
                'taken_sub_ranges': taken_sub_ranges,
                'time_slot_ranges': TIME_SLOT_RANGES,
                # Add pre-processed data
                'morning_ranges': TIME_SLOT_RANGES.get('morning', []),
                'afternoon_ranges': TIME_SLOT_RANGES.get('afternoon', []),
                'evening_ranges': TIME_SLOT_RANGES.get('evening', []),
                'morning_taken': taken_sub_ranges.get('morning', []),
                'afternoon_taken': taken_sub_ranges.get('afternoon', []),
                'evening_taken': taken_sub_ranges.get('evening', []),
            }
        except SolemnisationSlot.DoesNotExist:
            pass

    context = {
        'calendar_days': calendar_days,
        'month_name': calendar.month_name[month],
        'year': year,
        'month': month,
        'prev_month': month - 1 if month > 1 else 12,
        'prev_year': year if month > 1 else year - 1,
        'next_month': month + 1 if month < 12 else 1,
        'next_year': year if month < 12 else year + 1,
        'weekdays': ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
        'selected_date': selected_date,
        'time_slots': TIME_SLOT_CHOICES,
        'selected_date_details': selected_date_details,
        'username': user.username,
        'form_id': uuid.uuid4(),
        'groom_name': booking.groom_name,
        'bride_name': booking.bride_name,
        'booking': booking,
    }

    return render(request, 'editbooking.html', context)



def delete_booking(request, booking_id):
    # Check authentication and admin role
    if not request.session.get('user_id') or request.session.get('user_role') != 'adminchairman':
        messages.error(request, 'You need admin privileges to perform this action')
        return redirect('signin')
    
    try:
        # Get the booking to delete
        booking = SolemnisationBooking.objects.get(booking_id=booking_id)
        
        # Delete the booking
        booking.delete()
        messages.success(request, 'Booking deleted successfully!')
        
    except SolemnisationBooking.DoesNotExist:
        messages.error(request, 'Booking not found')
    except Exception as e:
        messages.error(request, f'Error deleting booking: {str(e)}')
    
    return redirect('booking_management')

def delete_timeslot(request, slot_id):
    if not request.session.get('user_id') or request.session.get('user_role') != 'adminchairman':
        messages.error(request, 'You need admin privileges to perform this action.')
        return redirect('signin')

    try:
        # Get the slot to delete
        slot = SolemnisationSlot.objects.get(id=slot_id)
        slot.delete()
        messages.success(request, 'Timeslot deleted successfully!')
    except SolemnisationSlot.DoesNotExist:
        messages.error(request, 'Timeslot not found.')
    except Exception as e:
        messages.error(request, f'Error deleting timeslot: {str(e)}')

    return redirect('solemnisation_management')


def view_approvebooking(request):
    if not request.session.get('user_id') or request.session.get('user_role') != 'adminchairman':
        return redirect('signin')
    
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('search', '')

    bookings = SolemnisationBooking.objects.filter(status='APPROVED').select_related('user').order_by('-updated_at')

    if status_filter:
        bookings = bookings.filter(status=status_filter)
    
    if search_query:
        bookings = bookings.filter(
            Q(booking_id__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(location__icontains=search_query)
        )

    #attach related assignments manually to each booking
    for booking in bookings:
        booking.assignments = ImamSolemnisationSchedule.objects.filter(booking=booking).select_related('imam')

    context = {
        'bookings': bookings,
        'status_filter': status_filter,
        'search_query': search_query,
    }
    return render(request, 'approvedbooking.html', context)




def assign_imam(request, booking_id):
    booking = get_object_or_404(SolemnisationBooking, booking_id=booking_id, status='APPROVED')
    
    if request.method == 'POST':
        imam_id = request.POST.get('imam')
        remarks = request.POST.get('remarks', '')
        
        if not imam_id:
            messages.error(request, "Please select an imam to assign")
            return redirect('assign_imam', booking_id=booking_id)
        
        imam = get_object_or_404(User, id=imam_id, role='imam')
        
        if ImamSolemnisationSchedule.objects.filter(imam=imam, booking=booking).exists():
            messages.warning(request, "This imam is already assigned to this booking")
            return redirect('assign_imam', booking_id=booking_id)
        
        booking_date = booking.booking_date
        booking_time_str = booking.time_slot
        
        availability = ImamAvailability.objects.filter(
            imam=imam,
            date=booking_date,
            status='available'
        ).first()
        
        if not availability:
            messages.warning(request, f"Imam {imam.fullname} is not available on {booking_date}")
            return redirect('assign_imam', booking_id=booking_id)
        
        if availability.time_slots:
            if booking_time_str not in availability.time_slots:
                messages.warning(request, f"Imam {imam.fullname} is not available at {booking_time_str}")
                return redirect('assign_imam', booking_id=booking_id)
        
        ImamSolemnisationSchedule.objects.create(
            imam=imam,
            booking=booking,
            remarks=remarks,
            status='PENDING'
        )
        
        messages.success(request, f"Imam {imam.fullname} has been assigned to this booking")
        return redirect('view_approvedbooking')
    
    imams = User.objects.filter(role='imam')
    existing_assignments = ImamSolemnisationSchedule.objects.filter(booking=booking)
    
    start_date = booking.booking_date - timedelta(days=7)
    end_date = booking.booking_date + timedelta(days=7)
    
    imam_availabilities = {}
    for imam in imams:
        availabilities = ImamAvailability.objects.filter(
            imam=imam,
            date__range=[start_date, end_date]
        ).order_by('date')
        
        availability_data = []
        for avail in availabilities:
            availability_data.append({
                'date': avail.date,
                'status': avail.status,
                'time_slots': avail.time_slots,
                'notes': avail.notes
            })
        
        imam_availabilities[imam.id] = availability_data
    
    context = {
        'booking': booking,
        'imams': imams,
        'existing_assignments': existing_assignments,
        'imam_availabilities': imam_availabilities,
        'booking_date': booking.booking_date,
        'booking_time': [booking.start_time, booking.end_time],
        'week_days': ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
    }
    return render(request, 'assignimam.html', context)

def imam_assignments(request):
    # Get the current imam user
    if not request.session.get('user_id') or request.session.get('user_role') != 'imam':
        return redirect('signin')
    
    # Get all assignments for this imam, ordered by booking date
    assignments = ImamSolemnisationSchedule.objects.filter(
        imam=User.objects.get(id=request.session['user_id'])
    ).select_related(
        'booking', 
    ).order_by('booking__booking_date')
    
    
    context = {
        'assignments': assignments,
    }
    
    return render(request, 'solemnisationsch.html', context)

def view_assignment(request, assignment_id):
    if not request.session.get('user_id') or request.session.get('user_role') != 'imam':
        return redirect('signin')
    
    try:
        assignment = ImamSolemnisationSchedule.objects.select_related(
            'booking', 'imam'
        ).get(
            id=assignment_id,
            imam_id=request.session['user_id']
        )
        
        # Get the imam's availability for the booking date
        booking_date = assignment.booking.booking_date
        imam_availability = ImamAvailability.objects.filter(
            imam=assignment.imam,
            date=booking_date
        ).first()
        
        # Get week days for the calendar display
        week_start = booking_date - timedelta(days=booking_date.weekday())
        week_days = [(week_start + timedelta(days=i)) for i in range(7)]
        
        # Get availability for the whole week
        week_availability = ImamAvailability.objects.filter(
            imam=assignment.imam,
            date__range=[week_start, week_start + timedelta(days=6)]
        ).order_by('date')
        
        context = {
            'assignment': assignment,
            'booking': assignment.booking,
            'imam_availability': imam_availability,
            'week_days': [day.strftime('%A') for day in week_days],
            'week_availability': week_availability,
            'booking_date': booking_date,
        }
        
        return render(request, 'confirmdatepage-imam.html', context)
        
    except ImamSolemnisationSchedule.DoesNotExist:
        messages.error(request, 'Assignment not found.')
        return redirect('imam_assignments')
    

def approve_schedule(request, assignment_id):
    if not request.session.get('user_id') or request.session.get('user_role') != 'imam':
        return redirect('signin')
    
    try:
        assignment = ImamSolemnisationSchedule.objects.get(
            id=assignment_id,
            imam_id=request.session['user_id'],
            status='PENDING'
        )
        
        # Update the schedule status to APPROVED
        assignment.status = 'APPROVED'
        assignment.save()
        
        messages.success(request, 'Schedule has been approved successfully.')
        return redirect('imam_assignments')
        
    except ImamSolemnisationSchedule.DoesNotExist:
        messages.error(request, 'Invalid assignment or already processed.')
        return redirect('imam_assignments')

def reject_schedule(request, assignment_id):
    if not request.session.get('user_id') or request.session.get('user_role') != 'imam':
        return redirect('signin')
    
    if request.method == 'POST':
        try:
            assignment = ImamSolemnisationSchedule.objects.get(
                id=assignment_id,
                imam_id=request.session['user_id'],
                status='PENDING'
            )
            
            remarks = request.POST.get('remarks', '').strip()
            if not remarks:
                messages.error(request, 'Remarks are required for rejection.')
                return redirect('view_assignment', assignment_id=assignment_id)
            
            # Update the schedule status to REJECTED and add remarks
            assignment.status = 'REJECTED'
            assignment.remarks = remarks
            assignment.save()
            
            messages.success(request, 'Schedule has been rejected.')
            return redirect('imam_assignments')
            
        except ImamSolemnisationSchedule.DoesNotExist:
            messages.error(request, 'Invalid assignment or already processed.')
            return redirect('imam_assignments')
    
    return redirect('imam_assignments')


def monthly_report(request):
    # Available years (current year and past 5 years)
    current_year = timezone.now().year
    years = range(current_year - 5, current_year + 1)
    
    # Month data
    months = [
        {'num': 1, 'name': 'January'},
        {'num': 2, 'name': 'February'},
        {'num': 3, 'name': 'March'},
        {'num': 4, 'name': 'April'},
        {'num': 5, 'name': 'May'},
        {'num': 6, 'name': 'June'},
        {'num': 7, 'name': 'July'},
        {'num': 8, 'name': 'August'},
        {'num': 9, 'name': 'September'},
        {'num': 10, 'name': 'October'},
        {'num': 11, 'name': 'November'},
        {'num': 12, 'name': 'December'},
    ]
    
    # Get selected year from URL parameter
    selected_year = request.GET.get('year', current_year)
    try:
        selected_year = int(selected_year)
    except (ValueError, TypeError):
        selected_year = current_year
    
    return render(request, 'monthlyreport.html', {
        'years': years,
        'months': months,
        'current_year': current_year,
        'selected_year': selected_year,
    })

def generate_monthly_report(request):
    if request.method == 'GET':
        try:
            year = int(request.GET.get('year'))
            month = int(request.GET.get('month'))
            report_date = datetime(year, month, 1).date()
        except (ValueError, TypeError):
            messages.error(request, "Invalid month or year specified")
            return redirect('monthly_report')
        
        # Calculate start and end dates for the month
        if month == 12:
            end_date = datetime(year+1, 1, 1).date()
        else:
            end_date = datetime(year, month+1, 1).date()
        
        # Get the current user
        try:
            admin_user = User.objects.get(pk=request.session.get('user_id'))
        except User.DoesNotExist:
            messages.error(request, "User not found")
            return redirect('monthly_report')
        
        # Get or create the report with UUID
        report, created = MonthlyReport.objects.get_or_create(
            month=report_date,
            admin=admin_user,
            defaults={
                'report_id': uuid.uuid4(),  # Add UUID for the report
                'total_applications': BrideGroomApplication.objects.filter(
                    created_at__gte=report_date,
                    created_at__lt=end_date
                ).count(),
                'approved_applications': BrideGroomApplication.objects.filter(
                    created_at__gte=report_date,
                    created_at__lt=end_date,
                    status='APPROVED'
                ).count(),
                'solemnisation_count': SolemnisationBooking.objects.filter(
                    booking_date__gte=report_date,
                    booking_date__lt=end_date
                ).count(),
            }
        )
        
        # If report exists, update it
        if not created:
            report.total_applications = BrideGroomApplication.objects.filter(
                created_at__gte=report_date,
                created_at__lt=end_date
            ).count()
            report.approved_applications = BrideGroomApplication.objects.filter(
                created_at__gte=report_date,
                created_at__lt=end_date,
                status='APPROVED'
            ).count()
            report.solemnisation_count = SolemnisationBooking.objects.filter(
                booking_date__gte=report_date,
                booking_date__lt=end_date
            ).count()
            report.save()
        
        month_name = report_date.strftime('%B %Y')
        messages.success(request, f"Report for {month_name} {'generated' if created else 'updated'} successfully")
    
    return redirect('report_detail', report_id=report.report_id)

def report_detail(request, report_id):
    try:
        report = MonthlyReport.objects.get(report_id=report_id)
        return render(request, 'generatereport.html', {'report': report})
    except MonthlyReport.DoesNotExist:
        messages.error(request, "Report not found")
        return redirect('monthly_report')
