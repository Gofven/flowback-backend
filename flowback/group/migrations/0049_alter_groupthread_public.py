from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('group', '0048_groupthread_public'),
    ]

    operations = [
        migrations.AlterField(
            model_name='groupthread',
            name='public',
            field=models.BooleanField(default=False),
        ),
    ]
