from django.contrib import admin

# Register your models here.
from .models import Submission, Challenge, Requirement

admin.site.register(Submission)

admin.site.register(Challenge)
admin.site.register(Requirement)
