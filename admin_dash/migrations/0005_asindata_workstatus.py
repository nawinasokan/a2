# Generated by Django 5.1.4 on 2025-01-20 10:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_dash', '0004_asindata_file_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='asindata',
            name='workstatus',
            field=models.CharField(default='Not Picked', max_length=50),
        ),
    ]
