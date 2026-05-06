from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0011_alter_personalevent_color_hex_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="recurringpersonalevent",
            name="color_hex",
            field=models.CharField(default="#8B5CF6", max_length=7),
        ),
    ]
