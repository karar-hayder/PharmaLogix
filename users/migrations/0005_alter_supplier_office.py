# Generated by Django 5.1.1 on 2024-10-27 21:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_supplier_created_at_supplier_office_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='supplier',
            name='office',
            field=models.CharField(blank=True, max_length=255, verbose_name='Office or dispensary'),
        ),
    ]
