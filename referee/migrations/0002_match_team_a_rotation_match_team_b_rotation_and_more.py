# Generated by Django 4.2 on 2025-06-05 22:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('referee', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='match',
            name='team_a_rotation',
            field=models.JSONField(default=list),
        ),
        migrations.AddField(
            model_name='match',
            name='team_b_rotation',
            field=models.JSONField(default=list),
        ),
        migrations.AlterField(
            model_name='action',
            name='action_type',
            field=models.CharField(choices=[('serve', 'Подача'), ('attack', 'Атака'), ('block', 'Блок'), ('receive', 'Прием'), ('set', 'Пас'), ('dig', 'Защита'), ('error', 'Ошибка')], max_length=12),
        ),
        migrations.AlterField(
            model_name='player',
            name='position',
            field=models.CharField(choices=[('s', 'связующий'), ('oh', 'доигровщик'), ('op', 'диагональный'), ('mb', 'центральный блокирующий'), ('l', 'либеро')], max_length=2, verbose_name='Позиция'),
        ),
    ]
