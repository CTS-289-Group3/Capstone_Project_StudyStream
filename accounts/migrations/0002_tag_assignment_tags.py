# accounts/migrations/0002_tag_assignment_tags.py
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('color_hex', models.CharField(default='#3b82f6', max_length=7)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tags', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['name'],
                'unique_together': {('user', 'name')},
            },
        ),
        migrations.AddField(
            model_name='assignment',
            name='tags',
            field=models.ManyToManyField(blank=True, related_name='assignments', to='accounts.Tag'),
        ),
        # Fix color_hex to remove choices constraint (allow any hex)
        migrations.AlterField(
            model_name='course',
            name='color_hex',
            field=models.CharField(default='#3b82f6', max_length=7),
        ),
        # Add quiz and homework to assignment type choices
        migrations.AlterField(
            model_name='assignment',
            name='assignment_type',
            field=models.CharField(
                choices=[
                    ('essay','Essay'),('exam','Exam'),('lab_report','Lab Report'),
                    ('problem_set','Problem Set'),('discussion','Discussion Post'),
                    ('project','Project'),('presentation','Presentation'),
                    ('reading','Reading'),('quiz','Quiz'),('homework','Homework'),('other','Other'),
                ],
                default='other', max_length=20
            ),
        ),
    ]