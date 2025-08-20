from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Zone',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('is_active', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='DrawType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.SlugField(max_length=30, unique=True)),
                ('name', models.CharField(max_length=100)),
                ('is_active', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='DrawSchedule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cutoff_time', models.TimeField(help_text='Hora de cierre de jugadas para este sorteo en esta zona')),
                ('is_active', models.BooleanField(default=True)),
                ('draw_type', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='schedules', to='catalog.drawtype')),
                ('zone', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='schedules', to='catalog.zone')),
            ],
            options={'unique_together': {('draw_type', 'zone')}},
        ),
        migrations.CreateModel(
            name='NumberLimit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.CharField(max_length=2)),
                ('max_pieces', models.PositiveIntegerField(default=0)),
                ('draw_type', models.ForeignKey(on_delete=models.deletion.CASCADE, to='catalog.drawtype')),
                ('zone', models.ForeignKey(on_delete=models.deletion.CASCADE, to='catalog.zone')),
            ],
            options={'unique_together': {('draw_type', 'zone', 'number')}},
        ),
    ]



