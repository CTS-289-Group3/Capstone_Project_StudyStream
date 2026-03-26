from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_profile'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='avatar_text',
            field=models.CharField(blank=True, max_length=2),
        ),
        migrations.AddField(
            model_name='profile',
            name='display_name',
            field=models.CharField(blank=True, max_length=50),
        ),
    ]
