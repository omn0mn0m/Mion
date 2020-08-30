from django.db import models

# Create your models here.
class User(models.Model):
    name = models.CharField(max_length=50)
    user_id = models.IntegerField()
    avatar_url = models.URLField(max_length=200)
    is_admin = models.BooleanField(default=False)

    def __str__(self):
        return self.name
    
