# Generated by Django 2.0 on 2018-01-23 21:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('logactivity', '0003_auto_20180122_1438'),
    ]

    operations = [
        migrations.AlterField(
            model_name='record',
            name='path',
            field=models.CharField(max_length=256),
        ),
        migrations.AlterField(
            model_name='record',
            name='query_string',
            field=models.CharField(max_length=256, null=True),
        ),
    ]