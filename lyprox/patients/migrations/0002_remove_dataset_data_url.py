# Generated by Django 4.2.7 on 2023-11-21 13:53

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('patients', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='dataset',
            name='data_url',
        ),
    ]
