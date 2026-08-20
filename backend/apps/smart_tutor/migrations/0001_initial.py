import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('ai', '0002_move_tutor_models'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.CreateModel(
                    name='TutorConversation',
                    fields=[
                        ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                        ('title', models.CharField(blank=True, max_length=200)),
                        ('created_at', models.DateTimeField(auto_now_add=True)),
                        ('updated_at', models.DateTimeField(auto_now=True)),
                        ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tutor_conversations', to=settings.AUTH_USER_MODEL)),
                    ],
                    options={'db_table': 'ai_tutorconversation'},
                ),
                migrations.CreateModel(
                    name='TutorMessage',
                    fields=[
                        ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                        ('role', models.CharField(choices=[('USER', 'User'), ('ASSISTANT', 'Assistant')], max_length=10)),
                        ('content', models.TextField()),
                        ('created_at', models.DateTimeField(auto_now_add=True)),
                        ('conversation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='smart_tutor.tutorconversation')),
                    ],
                    options={'db_table': 'ai_tutormessage'},
                ),
            ],
        ),
    ]
