# Generated by Django 4.2.5 on 2024-06-24 13:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('shewrote', '0018_work_date_of_publication_end_and_more'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='work',
            index=models.Index(fields=['title'], name='shewrote_wo_title_f525ff_idx'),
        ),
        migrations.AddIndex(
            model_name='work',
            index=models.Index(fields=['date_of_publication_start'], name='shewrote_wo_date_of_76ba2f_idx'),
        ),
        migrations.AddIndex(
            model_name='work',
            index=models.Index(fields=['date_of_publication_end'], name='shewrote_wo_date_of_e42c43_idx'),
        ),
    ]
