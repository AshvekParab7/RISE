from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('integrations', '0003_googlecalendar_googlecalendarevent_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='googlematerial',
            name='drive_file_id',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]