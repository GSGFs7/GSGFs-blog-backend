# Generated by Django 5.1.7 on 2025-03-27 15:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0028_remove_gal_name_gal_comprehensive_score_gal_title_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='gal',
            name='vndb_id',
            field=models.CharField(max_length=10, unique=True),
        ),
    ]
