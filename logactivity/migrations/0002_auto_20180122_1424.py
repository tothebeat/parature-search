# Generated by Django 2.0 on 2018-01-22 20:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('logactivity', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='record',
            name='query_string',
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name='record',
            name='user_address',
            field=models.GenericIPAddressField(null=True),
        ),
    ]
