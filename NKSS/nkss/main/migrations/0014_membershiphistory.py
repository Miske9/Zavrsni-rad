# Generated migration file
# Save as: main/migrations/0014_membershiphistory.py

from django.db import migrations, models
import django.db.models.deletion
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0013_player_is_active_member_player_member_since_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='MembershipHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(choices=[('ACTIVATED', 'Aktiviran'), ('DEACTIVATED', 'Deaktiviran'), ('REACTIVATED', 'Ponovno aktiviran'), ('EXTENDED', 'Produženo članstvo')], max_length=20)),
                ('date_from', models.DateField()),
                ('date_until', models.DateField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('notes', models.TextField(blank=True)),
                ('player', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='membership_history', to='main.player')),
            ],
            options={
                'verbose_name_plural': 'Membership histories',
                'ordering': ['-created_at'],
            },
        ),
    ]