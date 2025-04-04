# Generated by Django 4.2.5 on 2025-02-10 09:19

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('shewrote', '0045_alter_edition_related_work'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reception',
            name='document_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='shewrote.documenttype'),
        ),
        migrations.AlterField(
            model_name='reception',
            name='place_of_reception',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='shewrote.place'),
        ),
    ]
