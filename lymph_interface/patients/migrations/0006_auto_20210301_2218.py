# Generated by Django 3.1.6 on 2021-03-01 22:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('patients', '0005_auto_20210301_2135'),
    ]

    operations = [
        migrations.AlterField(
            model_name='patient',
            name='m_stage',
            field=models.PositiveSmallIntegerField(choices=[(0, 'M0'), (1, 'M1'), (2, 'MX')]),
        ),
    ]
