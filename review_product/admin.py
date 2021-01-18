from django.contrib import admin

# Register your models here.
from .models import  Review

class ReviewAdmin(admin.ModelAdmin):
    model = Review
    list_display = ('item', 'rating', 'user_name', 'comment', 'pub_date','tags')
    list_filter = ['pub_date', 'user_name']
    search_fields = ['comment']
    

admin.site.register(Review, ReviewAdmin)