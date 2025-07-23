# backend/orchestrator_api/migrations/0003_add_gceresult.py

from django.db import migrations, models
import django.db.models.deletion
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('orchestrator_api', '0003_rename_fingerprint_scan_id_port_idx_fingerprint_scan_id_970192_idx_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='GceResult',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('gce_task_id', models.UUIDField(blank=True, help_text='Task ID in Greenbone', null=True)),
                ('gce_report_id', models.UUIDField(blank=True, help_text='Report ID in Greenbone', null=True)),
                ('gce_target_id', models.UUIDField(blank=True, help_text='Target ID in Greenbone', null=True)),
                ('gce_scan_status', models.CharField(blank=True, help_text='Status from GCE (e.g., Running, Done, Stopped)', max_length=50, null=True)),
                ('gce_scan_progress', models.IntegerField(default=0, help_text='Scan progress percentage', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ('report_format', models.CharField(choices=[('XML', 'XML'), ('JSON', 'JSON')], default='XML', help_text='Format of the stored report', max_length=10)),
                ('full_report', models.TextField(blank=True, help_text='Full XML/JSON report from GCE', null=True)),
                ('vulnerability_count', models.JSONField(blank=True, default=dict, help_text='Count by severity: {critical: 0, high: 0, medium: 0, low: 0, log: 0}', null=True)),
                ('gce_scan_started_at', models.DateTimeField(blank=True, null=True)),
                ('gce_scan_completed_at', models.DateTimeField(blank=True, null=True)),
                ('scan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='gce_results', to='orchestrator_api.scan')),
                ('target', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='gce_results', to='orchestrator_api.target')),
            ],
            options={
                'verbose_name': 'GCE Result',
                'verbose_name_plural': 'GCE Results',
                'db_table': 'gce_result',
                'ordering': ['scan', 'created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='gceresult',
            index=models.Index(fields=['scan', 'gce_task_id'], name='gce_result_scan_id_gce_task_idx'),
        ),
        migrations.AddIndex(
            model_name='gceresult',
            index=models.Index(fields=['target'], name='gce_result_target_id_idx'),
        ),
    ]