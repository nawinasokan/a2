# Generated by Django 5.1.4 on 2025-01-24 12:14

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_dash', '0016_rename_asin_master_id_taskassign_asin_data_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='taskassign',
            name='region',
        ),
        migrations.RemoveField(
            model_name='taskassign',
            name='task_customer',
        ),
        migrations.RemoveField(
            model_name='taskassign',
            name='asin_data',
        ),
        migrations.RemoveField(
            model_name='taskassign',
            name='created_by',
        ),
        migrations.CreateModel(
            name='File_Upload',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key_asin', models.CharField(max_length=255)),
                ('candidate_asin', models.CharField(max_length=255)),
                ('region', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('file_name', models.CharField(blank=True, max_length=255, null=True)),
                ('l3_workstatus', models.CharField(default='Not Picked', max_length=50)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='task_created_by', to=settings.AUTH_USER_MODEL)),
                ('picked_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='asin_data_picked_by', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='L3_Production',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_time', models.DateTimeField(blank=True, null=True)),
                ('end_time', models.DateTimeField(blank=True, null=True)),
                ('que1', models.CharField(max_length=255, null=True)),
                ('que2', models.CharField(max_length=255, null=True)),
                ('que3', models.CharField(max_length=255, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('asin_master', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='asin_master_id', to='admin_dash.file_upload')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='l3_created_by', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='file_upload',
            name='l3_master',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='related_l3_data', to='admin_dash.l3_production'),
        ),
        migrations.DeleteModel(
            name='AsinData',
        ),
        migrations.DeleteModel(
            name='TaskAssign',
        ),
    ]
