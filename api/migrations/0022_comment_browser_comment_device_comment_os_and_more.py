# Generated by Django 5.1.6 on 2025-03-06 11:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0021_guest_avatar_guest_last_visit'),
    ]

    operations = [
        migrations.AddField(
            model_name='comment',
            name='browser',
            field=models.CharField(default=1, max_length=100),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='comment',
            name='device',
            field=models.CharField(default=1, max_length=100),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='comment',
            name='os',
            field=models.CharField(default=1, max_length=100),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='comment',
            name='user_agent',
            field=models.CharField(default=1, max_length=100),
            preserve_default=False,
        ),
    ]
