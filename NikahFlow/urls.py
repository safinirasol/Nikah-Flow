from django.urls import path
from . import views 


urlpatterns=[
    path("",views.homepage,name="homepage"),
    path("signup/",views.registration,name="signup"),
    path('login/', views.login, name='signin'),
    path('logout/',views.logout,name='logout'),
    path('account/admin/', views.admin_account, name='admin_account'),
    path('account/imam/', views.imam_account, name='imam_account'),
    path('account/bridegroom/', views.bridegroom_account, name='bridegroom_account'),
    path('admin/user-management/', views.user_management, name='user_management'),
    path('admin/create-user/', views.create_user, name='create_user'),
    path('admin/delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('admin/edit-user/<int:user_id>/', views.edit_user, name='edit_user'),

    path("bridegroom/submitapplication/",views.submit_application,name="submit_application"),
    path('bridegroom/track-application/', views.track_application, name='track_application'),

    path('imam/pending-applications/', views.pending_application, name='pending_application'),
    path('applications/<uuid:application_id>/', views.view_application, name='view_application'),
    path('application/approve/<uuid:application_id>/', views.approve_application, name='approve_application'),
    path('application/reject/<uuid:application_id>/', views.reject_application, name='reject_application'),

    path('imam/imam-schedule/', views.imam_scheduleimam, name='imam_scheduleimam'),
    path('admin/solemnnisation-schedule/', views.solemnisation_management, name='solemnisation_management'),
    path('admin/delete-timeslot/<int:slot_id>/', views.delete_timeslot, name='delete_timeslot'),


    path("bridegroom/submitbooking/",views.submit_booking,name="book_solemnisation"),
    path('bridegroom/track-booking/', views.track_booking, name='track_booking'),
    path('admin/solemnnisation-booking/', views.manage_bookings, name='booking_management'),
    path("admin/create-booking/",views.create_booking,name="create_booking"),
    path('admin/booking/<uuid:booking_id>/', views.view_booking, name='view_booking'),
    path('booking/approve/<uuid:booking_id>/', views.approve_booking, name='approve_booking'),
    path('booking/reject/<uuid:booking_id>/', views.reject_booking, name='reject_booking'),
    path('admin/edit-booking/<uuid:booking_id>/', views.edit_booking, name='edit_booking'),
    path('admin/delete-booking/<uuid:booking_id>/', views.delete_booking, name='delete_booking'),
    path('admin/approvedbooking/', views.view_approvebooking, name='view_approvedbooking'),
    path('admin/assign-approvedbooking/<uuid:booking_id>/', views.assign_imam, name='assign_imam'),
    path('imam/imam-assignments/', views.imam_assignments, name='imam_assignments'),
    path('imam/imam-assignments/<int:assignment_id>/', views.view_assignment, name='view_assignment'),
    path('imam/imam-assignments/approve/<int:assignment_id>/', views.approve_schedule, name='approve_schedule'),
    path('imam/imam-assignments/reject/<int:assignment_id>/', views.reject_schedule, name='reject_schedule'),

    path('admin/application-management/', views.manage_applications, name='application_management'),
    path('admin/create-application/', views.create_application, name='create_application'),
    path('admin/edit-application/<uuid:application_id>/', views.edit_application, name='edit_application'),
    path('admin/delete-application/<uuid:application_id>/', views.delete_application, name='delete_application'),

    path('admin/monthly-report/', views.monthly_report, name='monthly_report'),
    path('admin/monthly-report/generate/', views.generate_monthly_report, name='generate_report'),
    path('admin/monthly-report/generate/<uuid:report_id>', views.report_detail, name='report_detail'),
]