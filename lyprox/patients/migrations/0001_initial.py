# Generated by Django 4.2 on 2023-06-21 12:14

import django.db.models.deletion
from django.db import migrations, models

import lyprox.loggers
import lyprox.patients.fields
import lyprox.patients.mixins


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Dataset',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('git_repo_owner', models.CharField(default='rmnldwg', max_length=50)),
                ('git_repo_name', models.CharField(default='lydata.test', max_length=50)),
                ('revision', models.CharField(default='main', max_length=40)),
                ('data_path', models.CharField(default='2021-usz-oropharynx/data.csv', max_length=100)),
                ('data_url', models.URLField(max_length=400)),
                ('data_sha', models.CharField(max_length=40)),
                ('is_locked', models.BooleanField(default=False)),
                ('is_public', models.BooleanField(default=False)),
                ('date_created', models.DateTimeField()),
                ('is_outdated', models.BooleanField(default=False)),
                ('institution', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.institution')),
            ],
            options={
                'unique_together': {('git_repo_owner', 'git_repo_name', 'data_path')},
            },
            bases=(lyprox.loggers.ModelLoggerMixin, models.Model),
        ),
        migrations.CreateModel(
            name='Patient',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sex', models.CharField(choices=[('female', 'female'), ('male', 'male')], max_length=10)),
                ('age', models.IntegerField()),
                ('diagnose_date', lyprox.patients.fields.RobustDateField()),
                ('alcohol_abuse', models.BooleanField(blank=True, null=True)),
                ('nicotine_abuse', models.BooleanField(blank=True, null=True)),
                ('hpv_status', models.BooleanField(blank=True, null=True)),
                ('neck_dissection', models.BooleanField(blank=True, null=True)),
                ('tnm_edition', models.PositiveSmallIntegerField(default=8)),
                ('stage_prefix', models.CharField(choices=[('c', 'c'), ('p', 'p')], default='c', max_length=1)),
                ('t_stage', models.PositiveSmallIntegerField(choices=[(1, 'T1'), (2, 'T2'), (3, 'T3'), (4, 'T4')], default=0)),
                ('n_stage', models.PositiveSmallIntegerField(choices=[(0, 'N0'), (1, 'N1'), (2, 'N2'), (3, 'N3')], default=0)),
                ('m_stage', models.PositiveSmallIntegerField(choices=[(0, 'M0'), (1, 'M1'), (2, 'MX')], default=0)),
                ('dataset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='patients.dataset')),
            ],
            bases=(lyprox.patients.mixins.LockedDatasetMixin, lyprox.loggers.ModelLoggerMixin, models.Model),
        ),
        migrations.CreateModel(
            name='Tumor',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('location', models.CharField(choices=[('oral cavity', 'Oral Cavity'), ('oropharynx', 'Oropharynx'), ('hypopharynx', 'Hypopharynx'), ('larynx', 'Larynx')], max_length=20)),
                ('subsite', models.CharField(choices=[('oral cavity', (('C02', 'other parts of tongue'), ('C02.0', 'dorsal surface of tongue'), ('C02.1', 'border of tongue'), ('C02.2', 'ventral surface of tongue'), ('C02.3', 'anterior two thirds of tongue'), ('C02.4', 'lingual tonsil'), ('C02.8', 'overlapping sites of tongue'), ('C02.9', 'tongue, nos'), ('C03', 'gum'), ('C03.0', 'upper gum'), ('C03.1', 'lower gum'), ('C03.9', 'gum, nos'), ('C04', 'floor of mouth'), ('C04.0', 'anterior floor of mouth'), ('C04.1', 'lateral floor of mouth'), ('C04.8', 'overlapping lesion of floor of mouth'), ('C04.9', 'floor of mouth, nos'), ('C05', 'palate'), ('C05.0', 'hard palate'), ('C05.1', 'soft palate, nos'), ('C05.2', 'uvula'), ('C05.8', 'overlapping lesion of palate'), ('C05.9', 'palate, nos'), ('C06', 'other parts of mouth'), ('C06.0', 'cheeck mucosa'), ('C06.1', 'vestibule of mouth'), ('C06.2', 'retromolar area'), ('C06.8', 'overlapping lesion(s) of NOS parts of mouth'), ('C06.9', 'mouth, nos'), ('C07', 'parotid gland'), ('C08', 'other major salivary glands'), ('C08.0', 'submandibular gland'), ('C08.1', 'sublingual gland'), ('C08.9', 'salivary gland, nos'))), ('oropharynx', (('C01', 'base of tongue, nos'), ('C09', 'tonsil'), ('C09.0', 'tonsillar fossa'), ('C09.1', 'tonsillar pillar'), ('C09.8', 'overlapping lesion of tonsil'), ('C09.9', 'tonsil, nos'), ('C10', 'oropharynx'), ('C10.0', 'vallecula'), ('C10.1', 'anterior surface of epiglottis'), ('C10.2', 'lateral wall of oropharynx'), ('C10.3', 'posterior wall of oropharynx'), ('C10.4', 'branchial cleft'), ('C10.8', 'overlapping lesions of oropharynx'), ('C10.9', 'oropharynx, nos'))), ('hypopharynx', (('C12', 'pyriform sinus'), ('C13', 'hypopharynx'), ('C13.0', 'postcricoid region'), ('C13.1', 'hypopharyngeal aspect of aryepiglottic fold'), ('C13.2', 'posterior wall of hypopharynx'), ('C13.8', 'overlapping lesion of hypopharynx'), ('C13.9', 'hypopharynx, nos'))), ('larynx', (('C32', 'larynx'), ('C32.0', 'glottis'), ('C32.1', 'supraglottis'), ('C32.2', 'subglottis'), ('C32.3', 'laryngeal cartilage'), ('C32.8', 'overlapping lesion of larynx'), ('C32.9', 'larynx, nos')))], max_length=10)),
                ('central', models.BooleanField(blank=True, null=True)),
                ('extension', models.BooleanField(blank=True, null=True)),
                ('volume', models.FloatField(blank=True, null=True)),
                ('t_stage', models.PositiveSmallIntegerField(choices=[(1, 'T1'), (2, 'T2'), (3, 'T3'), (4, 'T4')])),
                ('stage_prefix', models.CharField(choices=[('c', 'c'), ('p', 'p')], max_length=1)),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='patients.patient')),
            ],
            bases=(lyprox.patients.mixins.LockedDatasetMixin, lyprox.loggers.ModelLoggerMixin, models.Model),
        ),
        migrations.CreateModel(
            name='Diagnose',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('modality', models.CharField(choices=[('CT', 'CT'), ('MRI', 'MRI'), ('PET', 'PET'), ('FNA', 'Fine Needle Aspiration'), ('diagnostic_consensus', 'Diagnostic Consensus'), ('pathology', 'Pathology'), ('pCT', 'Planning CT')], max_length=20)),
                ('diagnose_date', lyprox.patients.fields.RobustDateField(blank=True, null=True)),
                ('side', models.CharField(choices=[('ipsi', 'ipsi'), ('contra', 'contra')], max_length=10)),
                ('I', models.BooleanField(blank=True, null=True)),
                ('Ia', models.BooleanField(blank=True, null=True)),
                ('Ib', models.BooleanField(blank=True, null=True)),
                ('II', models.BooleanField(blank=True, null=True)),
                ('IIa', models.BooleanField(blank=True, null=True)),
                ('IIb', models.BooleanField(blank=True, null=True)),
                ('III', models.BooleanField(blank=True, null=True)),
                ('IV', models.BooleanField(blank=True, null=True)),
                ('V', models.BooleanField(blank=True, null=True)),
                ('Va', models.BooleanField(blank=True, null=True)),
                ('Vb', models.BooleanField(blank=True, null=True)),
                ('VII', models.BooleanField(blank=True, null=True)),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='patients.patient')),
            ],
            bases=(lyprox.patients.mixins.LockedDatasetMixin, lyprox.loggers.ModelLoggerMixin, models.Model),
        ),
    ]