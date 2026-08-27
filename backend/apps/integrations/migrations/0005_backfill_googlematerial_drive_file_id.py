from urllib.parse import parse_qs, urlparse

from django.db import migrations


def drive_id_from_url(value):
    if not value:
        return ''
    parsed = urlparse(value)
    query_id = parse_qs(parsed.query).get('id', [''])[-1]
    if query_id:
        return query_id
    parts = [part for part in parsed.path.split('/') if part]
    for marker in ('d', 'file'):
        if marker in parts:
            index = parts.index(marker)
            if index + 1 < len(parts):
                return parts[index + 1]
    return ''


def backfill_drive_file_ids(apps, schema_editor):
    GoogleMaterial = apps.get_model('integrations', 'GoogleMaterial')
    for material in GoogleMaterial.objects.filter(drive_file_id='').exclude(source_url='').iterator():
        drive_file_id = drive_id_from_url(material.source_url)
        if drive_file_id:
            material.drive_file_id = drive_file_id
            material.save(update_fields=('drive_file_id',))


class Migration(migrations.Migration):
    dependencies = [
        ('integrations', '0004_googlematerial_drive_file_id'),
    ]

    operations = [
        migrations.RunPython(backfill_drive_file_ids, migrations.RunPython.noop),
    ]
