# Generated by Django 2.2.13 on 2020-06-30 04:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('awc', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='submission',
            name='submission_comment_id',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
