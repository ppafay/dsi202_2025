# Generated by Django 5.2 on 2025-04-16 21:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('outfits', '0010_alter_outfit_price'),
    ]

    operations = [
        migrations.AlterField(
            model_name='outfit',
            name='price',
            field=models.FloatField(default=0.0),
        ),
    ]
