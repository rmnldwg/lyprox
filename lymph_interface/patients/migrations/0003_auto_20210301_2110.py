# Generated by Django 3.1.6 on 2021-03-01 21:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('patients', '0002_auto_20210301_2109'),
    ]

    operations = [
        migrations.AlterField(
            model_name='diagnose',
            name='modality',
            field=models.PositiveSmallIntegerField(choices=[(0, 'CT'), (1, 'MRI'), (2, 'PET'), (3, 'FNA'), (4, 'path')]),
        ),
    ]