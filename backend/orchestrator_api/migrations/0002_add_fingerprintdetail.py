from django.db import migrations, models
import django.db.models.deletion
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('orchestrator_api', '0001_initial'),  # Replace with your latest migration
    ]

    operations = [
        migrations.CreateModel(
            name='FingerprintDetail',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('port', models.IntegerField()),
                ('protocol', models.CharField(choices=[('tcp', 'TCP'), ('udp', 'UDP')], default='tcp', max_length=10)),
                ('service_name', models.CharField(blank=True, max_length=100, null=True)),
                ('service_version', models.CharField(blank=True, max_length=255, null=True)),
                ('service_product', models.CharField(blank=True, max_length=255, null=True)),
                ('service_info', models.TextField(blank=True, null=True)),
                ('fingerprint_method', models.CharField(help_text='Method used for fingerprinting (e.g., fingerprintx, banner)', max_length=50)),
                ('confidence_score', models.IntegerField(default=0, help_text='Confidence score 0-100', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ('raw_response', models.TextField(blank=True, null=True)),
                ('additional_info', models.JSONField(blank=True, null=True)),
                ('scan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fingerprint_details', to='orchestrator_api.scan')),
                ('target', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fingerprint_details', to='orchestrator_api.target')),
            ],
            options={
                'verbose_name': 'Fingerprint Detail',
                'verbose_name_plural': 'Fingerprint Details',
                'db_table': 'fingerprint_detail',
                'ordering': ['scan', 'port'],
            },
        ),
        migrations.AddIndex(
            model_name='fingerprintdetail',
            index=models.Index(fields=['scan', 'port'], name='fingerprint_scan_id_port_idx'),
        ),
        migrations.AddIndex(
            model_name='fingerprintdetail',
            index=models.Index(fields=['target', 'port'], name='fingerprint_target_id_port_idx'),
        ),
    ]