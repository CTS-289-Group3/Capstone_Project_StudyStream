import uuid

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_assignment_schema_and_course_palette'),
    ]

    operations = [
        migrations.AddField(
            model_name='assignmentsubtask',
            name='subtask_id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
        migrations.RenameField(
            model_name='assignmentsubtask',
            old_name='sequence_order',
            new_name='step_order',
        ),
        migrations.RenameField(
            model_name='assignmentsubtask',
            old_name='milestone_date',
            new_name='due_date',
        ),
        migrations.AddField(
            model_name='assignmentsubtask',
            name='due_time',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='assignmentsubtask',
            name='completion_percentage',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterModelOptions(
            name='assignmentsubtask',
            options={'ordering': ['step_order']},
        ),
    ]
