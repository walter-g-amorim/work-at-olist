# Generated by Django 2.0.6 on 2018-06-08 20:44

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rest', '0003_auto_20180608_1658'),
    ]

    operations = [
        migrations.RenameField(
            model_name='callrecord',
            old_name='destination_number',
            new_name='destination',
        ),
        migrations.RenameField(
            model_name='callrecord',
            old_name='source_number',
            new_name='source',
        ),
        migrations.RenameField(
            model_name='callrecord',
            old_name='record_timestamp',
            new_name='timestamp',
        ),
    ]