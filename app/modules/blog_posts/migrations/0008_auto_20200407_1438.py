# Generated by Django 3.0.4 on 2020-04-07 14:38

from django.conf import settings
from django.db import migrations
import modelcluster.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('blog_posts', '0007_merge_20200407_0838'),
    ]

    operations = [
        migrations.AlterField(
            model_name='blogpost',
            name='authors',
            field=modelcluster.fields.ParentalManyToManyField(related_name='pages_blogpost', to=settings.AUTH_USER_MODEL),
        ),
    ]
