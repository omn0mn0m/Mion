# Generated by Django 2.2.13 on 2020-09-05 06:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('awc', '0012_challenge_archived'),
    ]

    operations = [
        migrations.AlterField(
            model_name='challenge',
            name='prerequisites',
            field=models.ManyToManyField(blank=True, to='awc.Challenge'),
        ),
    ]
