# Generated by Django 4.2.5 on 2024-05-30 09:08

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shewrote', '0010_rename_typeofcollective_collectivetype'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='TypeOfDocument',
            new_name='DocumentType',
        ),
    ]