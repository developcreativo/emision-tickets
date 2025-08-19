import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('catalog', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Ticket',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('total_pieces', models.PositiveIntegerField(default=0)),
                ('draw_type', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='catalog.drawtype')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
                ('zone', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='catalog.zone')),
            ],
        ),
        migrations.CreateModel(
            name='TicketItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.CharField(max_length=2)),
                ('pieces', models.PositiveIntegerField(default=1)),
                ('ticket', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='sales.ticket')),
            ],
            options={'unique_together': {('ticket', 'number')}},
        ),
    ]



