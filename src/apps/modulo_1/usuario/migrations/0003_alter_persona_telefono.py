from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('usuario', '0002_alter_persona_correo'),
    ]

    operations = [
        migrations.AlterField(
            model_name='persona',
            name='telefono',
            field=models.CharField(blank=True, max_length=30, null=True, verbose_name='Teléfono'),
        ),
    ]
