# Generated by Django 5.1.4 on 2025-01-24 11:24

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('admin_dash', '0014_asindata_task_assign'),
    ]

    operations = [
        migrations.RenameField(
            model_name='taskassign',
            old_name='asin_data',
            new_name='asin_master_id',
        ),
        migrations.RemoveField(
            model_name='taskassign',
            name='region',
        ),
        migrations.RemoveField(
            model_name='taskassign',
            name='task_customer',
        ),
    ]
