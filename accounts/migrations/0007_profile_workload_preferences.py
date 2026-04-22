from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_subtask_schema_upgrade'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='commute_time_hours_per_week',
            field=models.DecimalField(decimal_places=1, default=0.0, max_digits=4, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(168)]),
        ),
        migrations.AddField(
            model_name='profile',
            name='family_time_hours_per_week',
            field=models.DecimalField(decimal_places=1, default=0.0, max_digits=4, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(168)]),
        ),
        migrations.AddField(
            model_name='profile',
            name='personal_time_hours_per_week',
            field=models.DecimalField(decimal_places=1, default=14.0, max_digits=4, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(168)]),
        ),
        migrations.AddField(
            model_name='profile',
            name='sleep_end_time',
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='sleep_hours_per_night',
            field=models.DecimalField(decimal_places=1, default=7.0, max_digits=3, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(24)]),
        ),
        migrations.AddField(
            model_name='profile',
            name='sleep_start_time',
            field=models.TimeField(blank=True, null=True),
        ),
    ]
