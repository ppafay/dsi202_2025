# Generated by Django 5.2 on 2025-04-16 16:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('outfits', '0005_outfit_price_alter_outfit_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='outfit',
            name='rent_duration',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='outfit',
            name='image',
            field=models.ImageField(default=500, upload_to='outfits/'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='outfit',
            name='name',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='outfit',
            name='price',
            field=models.DecimalField(decimal_places=2, max_digits=8),
        ),
    ]
