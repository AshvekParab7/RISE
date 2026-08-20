from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('ai', '0001_initial'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.DeleteModel(name='TutorMessage'),
                migrations.DeleteModel(name='TutorConversation'),
            ],
            database_operations=[],
        ),
    ]
