# Generated by Django 3.1.6 on 2021-03-01 21:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('patients', '0004_auto_20210301_2114'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tumor',
            name='extension',
            field=models.BooleanField(blank=True, null=True),
        ),
    ]