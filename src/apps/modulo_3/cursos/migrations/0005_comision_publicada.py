from django.db import migrations, models


def publicar_comisiones_existentes(apps, schema_editor):
    Comision = apps.get_model('cursos', 'Comision')
    Comision.objects.all().update(publicada=True)


class Migration(migrations.Migration):
    dependencies = [
        ('cursos', '0004_curso_edad_maxima_alter_comision_cupo_maximo_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='comision',
            name='publicada',
            field=models.BooleanField(default=False, verbose_name='Publicada'),
        ),
        migrations.RunPython(publicar_comisiones_existentes, migrations.RunPython.noop),
    ]

