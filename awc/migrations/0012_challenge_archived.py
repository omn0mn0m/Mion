# Generated by Django 2.2.13 on 2020-09-05 05:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('awc', '0011_requirement_raw_requirement'),
    ]

    operations = [
        migrations.AddField(
            model_name='challenge',
            name='archived',
            field=models.BooleanField(default=False),
        ),
    ]
