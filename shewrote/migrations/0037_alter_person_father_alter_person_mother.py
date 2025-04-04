# Generated by Django 4.2.5 on 2025-01-27 08:35

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('shewrote', '0036_alter_person_place_of_death'),
    ]

    operations = [
        migrations.AlterField(
            model_name='person',
            name='father',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='father_of', to='shewrote.person'),
        ),
        migrations.AlterField(
            model_name='person',
            name='mother',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='mother_of', to='shewrote.person'),
        ),
    ]
