# Generated by Django 4.2.5 on 2024-01-24 15:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shewrote', '0004_alter_periodofresidence_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='person',
            name='place_of_residence_notes',
            field=models.TextField(blank=True),
        ),
    ]