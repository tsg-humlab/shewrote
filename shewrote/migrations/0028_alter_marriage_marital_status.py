# Generated by Django 4.2.5 on 2024-11-26 09:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shewrote', '0027_person_shewrote_pe_normali_6b613d_idx_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='marriage',
            name='marital_status',
            field=models.CharField(blank=True, choices=[('M', 'Married'), ('D', 'Divorced'), ('W', 'Widowed'), ('U', 'Unmarried'), ('L', 'Living together'), ('O', 'Other')], max_length=1),
        ),
    ]
