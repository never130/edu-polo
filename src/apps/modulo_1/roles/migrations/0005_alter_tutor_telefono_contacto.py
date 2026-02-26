from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('roles', '0004_autorizadoretiro'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tutor',
            name='telefono_contacto',
            field=models.CharField(max_length=30),
        ),
    ]
