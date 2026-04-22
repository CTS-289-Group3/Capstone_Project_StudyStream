from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_profile_workload_preferences'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='weekly_study_hours',
            field=models.DecimalField(decimal_places=1, default=0, max_digits=4, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(168)]),
        ),
    ]
