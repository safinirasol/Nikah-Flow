from django.contrib import admin

# Register your models here.
from .models import User,BrideGroomApplication, ImamAvailability,SolemnisationSlot,SolemnisationBooking

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id_number', 'username', 'email', 'fullname', 'role', 'phone_number', 'status')
    search_fields = ('username', 'email', 'fullname')
    list_filter = ('role', 'status')

@admin.register(BrideGroomApplication)
class BrideGroomApplicationAdmin(admin.ModelAdmin):
    list_display = ('application_id', 'get_username', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('application_id', 'groom_fullname', 'bride_fullname', 'user__username')

    def get_username(self, obj):
        return obj.user.username if obj.user else '-'
    get_username.short_description = 'Username'


@admin.register(ImamAvailability)
class ImamScheduleAdmin(admin.ModelAdmin):
    list_display = ('imam', 'date', 'status', 'time_slots', 'notes')
    list_filter = ('imam', 'status')

@admin.register(SolemnisationSlot)
class SolemnisationSlotAdmin(admin.ModelAdmin):
    list_display = ( 'date', 'status', 'time_slots', 'notes')
    list_filter = ( 'date', 'status')

@admin.register(SolemnisationBooking)
class BrideGroomBookingAdmin(admin.ModelAdmin):
    list_display = ('groom_name','bride_name','booking_id', 'get_username', 'status','booking_date' ,'time_slot','start_time','end_time','location','created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('booking_id',  'user__username')

    def get_username(self, obj):
        return obj.user.username if obj.user else '-'
    get_username.short_description = 'Username'