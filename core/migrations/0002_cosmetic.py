# Generated by Django 5.1.1 on 2024-10-21 13:00

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Cosmetic',
            fields=[
                ('product_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='core.product')),
                ('brand', models.CharField(max_length=200)),
                ('type', models.CharField(max_length=100)),
                ('ingredients', models.TextField(blank=True)),
            ],
            bases=('core.product',),
        ),
    ]
