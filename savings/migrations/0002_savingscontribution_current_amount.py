# Generated by Django 5.2 on 2025-04-26 17:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('savings', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='savingscontribution',
            name='current_amount',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
    ]
