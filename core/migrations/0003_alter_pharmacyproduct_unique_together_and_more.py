# Generated by Django 5.1.1 on 2024-10-27 20:26

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_cosmetic'),
        ('users', '0004_supplier_created_at_supplier_office_and_more'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='pharmacyproduct',
            unique_together=set(),
        ),
        migrations.AddField(
            model_name='pharmacyproduct',
            name='supplier',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='users.supplier'),
        ),
        migrations.AlterUniqueTogether(
            name='pharmacyproduct',
            unique_together={('product', 'pharmacy', 'supplier')},
        ),
    ]