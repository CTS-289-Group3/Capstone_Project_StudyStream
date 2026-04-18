import uuid

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_profile_display_name_avatar_text'),
    ]

    operations = [
        migrations.AlterField(
            model_name='course',
            name='color_hex',
            field=models.CharField(
                choices=[
                    ('#DC143C', 'Crimson (Red Pin)'),
                    ('#1E90FF', 'Ocean (Blue Pin)'),
                    ('#228B22', 'Forest (Green Pin)'),
                    ('#FFD700', 'Sunflower (Yellow Pin)'),
                    ('#8B00FF', 'Violet (Purple Pin)'),
                    ('#FF8C00', 'Tangerine (Orange Pin)'),
                    ('#008080', 'Teal (Teal Pin)'),
                    ('#FF69B4', 'Rose (Pink Pin)'),
                ],
                default='#1E90FF',
                max_length=7,
            ),
        ),
        migrations.AddField(
            model_name='assignment',
            name='assignment_id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
        migrations.RenameField(
            model_name='assignment',
            old_name='priority',
            new_name='priority_level',
        ),
        migrations.RenameField(
            model_name='assignment',
            old_name='is_major',
            new_name='is_major_project',
        ),
        migrations.RenameField(
            model_name='assignment',
            old_name='completion_pct',
            new_name='completion_percentage',
        ),
        migrations.AddField(
            model_name='assignment',
            name='contributes_to_workload',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='assignment',
            name='due_time',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='assignment',
            name='submission_link',
            field=models.URLField(blank=True),
        ),
        migrations.AlterField(
            model_name='assignment',
            name='assignment_type',
            field=models.CharField(
                choices=[
                    ('essay', 'Essay'),
                    ('exam', 'Exam'),
                    ('lab_report', 'Lab Report'),
                    ('problem_set', 'Problem Set'),
                    ('discussion', 'Discussion Post'),
                    ('project', 'Project'),
                    ('presentation', 'Presentation'),
                    ('reading', 'Reading'),
                    ('quiz', 'Quiz'),
                    ('homework', 'Homework'),
                    ('other', 'Other'),
                ],
                default='other',
                max_length=50,
            ),
        ),
        migrations.AlterField(
            model_name='assignment',
            name='estimated_hours',
            field=models.DecimalField(blank=True, decimal_places=1, max_digits=4, null=True),
        ),
    ]
