import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('integrations', '0005_backfill_googlematerial_drive_file_id'),
        ('tasks', '0005_studysession_tab_switch_count'),
    ]

    operations = [
        migrations.CreateModel(
            name='WhatsAppAssignmentReminder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sent_at', models.DateTimeField(blank=True, null=True)),
                ('message_sid', models.CharField(blank=True, max_length=64)),
                ('error', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('task', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='whatsapp_reminder', to='tasks.task')),
            ],
            options={'ordering': ('-updated_at',)},
        ),
    ]