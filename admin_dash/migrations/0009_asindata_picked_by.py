# Generated by Django 5.1.4 on 2025-01-21 03:31

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_dash', '0008_taskassign'),
    ]

    operations = [
        migrations.AddField(
            model_name='asindata',
            name='picked_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='asin_data_picked_by', to=settings.AUTH_USER_MODEL),
        ),
    ]
