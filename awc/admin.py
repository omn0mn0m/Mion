from django.contrib import admin

# Register your models here.
from .models import User, Submission, Challenge, Requirement

admin.site.register(User)
admin.site.register(Submission)

admin.site.register(Challenge)
admin.site.register(Requirement)
