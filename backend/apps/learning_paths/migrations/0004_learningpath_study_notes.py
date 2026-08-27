from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('learning_paths', '0003_learninglevel_best_stars')]

    operations = [migrations.AddField(model_name='learningpath', name='study_notes', field=models.JSONField(default=list))]