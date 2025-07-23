# plugins/gce_scanner/TROUBLESHOOTING.md

# GCE Scanner Troubleshooting Guide

## Common Issues and Solutions

### 1. GMP Version Incompatibility

**Error**: `Remote manager daemon uses an unsupported version of GMP. The GMP version was X.X`

**Cause**: The python-gvm library version doesn't support the GMP protocol version used by your GCE installation.

**Solutions**:

1. **Run the debug script** to understand the issue:
   ```bash
   docker-compose exec gce_scanner python debug_gmp.py
   ```

2. **Rebuild the container**:
   ```bash
   chmod +x update-gce-scanner.sh
   ./update-gce-scanner.sh
   ```

3. **Try alternative requirements** (uses latest python-gvm from GitHub):
   ```bash
   docker-compose exec gce_scanner pip install -r requirements-alt.txt
   docker-compose restart gce_scanner
   ```

4. **Manual fix** - Install specific python-gvm version:
   ```bash
   # For GMP 22.x
   docker-compose exec gce_scanner pip uninstall -y python-gvm
   docker-compose exec gce_scanner pip install git+https://github.com/greenbone/python-gvm.git@main
   docker-compose restart gce_scanner
   ```

5. **Check GMP protocol version**:
   ```bash
   docker-compose exec gce_scanner python -c "
   from gvm.connections import UnixSocketConnection
   from gvm.protocols.gmp import Gmp
   from gvm.transforms import EtreeCheckCommandTransform
   import os
   
   connection = UnixSocketConnection('/mnt/gce_sockets/gvmd.sock')
   gmp = Gmp(connection, EtreeCheckCommandTransform())
   
   with gmp:
       gmp.authenticate(os.environ['GCE_USERNAME'], os.environ['GCE_PASSWORD'])
       version = gmp.get_version()
       print(version.find('version').text)
   "
   ```

### 2. ModuleNotFoundError for gmpv224

**Error**: `ModuleNotFoundError: No module named 'gvm.protocols.gmpv224'`

**Cause**: The specific protocol version module doesn't exist in python-gvm.

**Solution**: The code has been updated to use the standard GMP protocol which should handle version negotiation automatically.

### 2. Socket Not Found

**Error**: `Socket file not found: /mnt/gce_sockets/gvmd.sock`

**Solutions**:

1. **Check if GCE is running**:
   ```bash
   cd gce
   docker compose -f docker-compose-gce.yml ps
   ```

2. **Verify socket location in GCE container**:
   ```bash
   docker compose -f docker-compose-gce.yml exec gvmd ls -la /run/gvmd/
   ```

3. **Check volume mounting**:
   ```bash
   docker inspect vapter_gce_scanner | grep -A 10 Mounts
   ```

4. **Ensure volume exists**:
   ```bash
   docker volume ls | grep gvmd_socket_vol
   ```

### 3. Authentication Failed

**Error**: `GVM Error: Authentication failed`

**Solutions**:

1. **Verify credentials match between VaPtER and GCE**:
   ```bash
   # Check VaPtER configuration
   grep GCE_USERNAME .env
   grep GCE_PASSWORD .env
   
   # Check GCE configuration
   cd gce
   grep GCE_VAPTER_USER .env.gce
   grep GCE_VAPTER_PASSWORD .env.gce
   ```

2. **Create/update user in GCE**:
   ```bash
   cd gce
   docker compose -f docker-compose-gce.yml exec -u gvmd gvmd \
     gvmd --create-user=vapter_api --password=your_password
   ```

3. **List existing users**:
   ```bash
   docker compose -f docker-compose-gce.yml exec -u gvmd gvmd \
     gvmd --get-users
   ```

### 4. Scan Takes Too Long or Times Out

**Error**: Scan timeout reached

**Solutions**:

1. **Increase timeout** in `.env`:
   ```bash
   GCE_MAX_SCAN_TIME=28800  # 8 hours
   ```

2. **Check GCE performance**:
   ```bash
   # Monitor GCE resource usage
   docker stats $(docker compose -f gce/docker-compose-gce.yml ps -q)
   ```

3. **Reduce scan scope**:
   - Use a smaller port list
   - Scan fewer hosts at once

### 5. Report Format Issues

**Error**: Failed to parse report

**Solutions**:

1. **Check report format configuration**:
   ```bash
   grep GCE_REPORT_FORMAT .env
   ```

2. **Test report retrieval manually**:
   ```bash
   docker-compose exec gce_scanner python -c "
   # Test script to retrieve a report
   # (insert test code here)
   "
   ```

### 6. RabbitMQ Connection Issues

**Error**: Failed to connect to RabbitMQ

**Solutions**:

1. **Check RabbitMQ is running**:
   ```bash
   docker-compose ps rabbitmq
   ```

2. **Test RabbitMQ connection**:
   ```bash
   docker-compose exec gce_scanner python -c "
   import pika
   import os
   url = os.environ.get('RABBITMQ_URL')
   connection = pika.BlockingConnection(pika.URLParameters(url))
   print('Connected to RabbitMQ!')
   connection.close()
   "
   ```

### 7. Memory Issues

**Error**: Container killed or OOM errors

**Solutions**:

1. **Increase container memory limits** in docker-compose.yml:
   ```yaml
   gce_scanner:
     mem_limit: 2g
     memswap_limit: 2g
   ```

2. **Monitor memory usage**:
   ```bash
   docker stats vapter_gce_scanner
   ```

## Debug Mode

To enable verbose logging:

1. **Set LOG_LEVEL in .env**:
   ```bash
   LOG_LEVEL=DEBUG
   ```

2. **Restart the container**:
   ```bash
   docker-compose restart gce_scanner
   ```

3. **View detailed logs**:
   ```bash
   docker-compose logs -f gce_scanner
   ```

## Manual Testing

### Test GCE Connection
```bash
docker-compose exec gce_scanner python test_gce.py
```

### Send Test Scan Request
```bash
docker-compose exec backend python test_gce_integration.py
```

### Direct GMP Commands
```bash
docker-compose exec gce_scanner python -c "
from test_gce import get_gmp_connection
import os

with get_gmp_connection() as gmp:
    gmp.authenticate(os.environ['GCE_USERNAME'], os.environ['GCE_PASSWORD'])
    
    # Get version
    version = gmp.get_version()
    print('GMP Version:', version.find('version').text)
    
    # List first 5 targets
    targets = gmp.get_targets()
    for i, target in enumerate(targets.findall('target')[:5]):
        print(f\"{i+1}. {target.find('name').text}\")
"
```

## Performance Tuning

### Optimize Scan Performance

1. **Adjust polling interval**:
   ```bash
   GCE_POLLING_INTERVAL=30  # Check more frequently
   ```

2. **Use appropriate scan configs**:
   - "Full and fast" for general scans
   - "Discovery" for quick host detection
   - Custom configs for specific needs

3. **Limit concurrent scans**:
   - GCE can handle limited concurrent scans
   - Queue additional scans in RabbitMQ

## Getting Help

1. **Check logs first**:
   ```bash
   docker-compose logs --tail=100 gce_scanner
   ```

2. **Enable debug mode** (see above)

3. **Test components individually**:
   - GCE connection
   - RabbitMQ connection
   - API Gateway connection

4. **Verify configurations** match between services

5. **Check GCE documentation**: https://greenbone.github.io/docs/