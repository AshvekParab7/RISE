from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('tasks', '0004_studysession_smart_break_test'),
    ]

    operations = [
        migrations.AddField(
            model_name='studysession',
            name='tab_switch_count',
            field=models.PositiveIntegerField(default=0),
        ),
    ]