# Generated by Django 4.2.5 on 2024-06-24 09:01

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('shewrote', '0017_reception_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='work',
            name='date_of_publication_end',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='work',
            name='date_of_publication_start',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='work',
            name='date_of_publication_text',
            field=models.CharField(blank=True, max_length=128),
        ),
    ]
