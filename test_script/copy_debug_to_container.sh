#!/bin/bash
# copy_debug_to_container.sh - Copy debug script to API Gateway container

echo "📋 Copying debug script to API Gateway container..."

# Create debug script in container
docker-compose exec api_gateway bash -c 'cat > debug_config.py << "EOF"
import os
import sys
import json

print("🔍 API Gateway Configuration Debug")
print("================================")

# Print all environment variables related to the gateway
print("\n📊 Environment Variables:")
print("-" * 25)
for key, value in sorted(os.environ.items()):
    if any(keyword in key.upper() for keyword in ["CORS", "BACKEND", "DEBUG", "LOG", "SECRET", "GATEWAY"]):
        print(f"{key}: {value}")

print("\n🔧 Loading Configuration...")
print("-" * 25)

try:
    # Try to import the config
    from app.config import settings
    
    print("✅ Configuration loaded successfully!")
    print(f"Project Name: {settings.PROJECT_NAME}")
    print(f"Version: {settings.VERSION}")
    print(f"Debug: {settings.DEBUG}")
    print(f"Log Level: {settings.LOG_LEVEL}")
    print(f"Backend URL: {settings.BACKEND_URL}")
    print(f"Backend Timeout: {settings.BACKEND_TIMEOUT}")
    print(f"CORS Origins (raw): {settings.CORS_ALLOWED_ORIGINS}")
    print(f"CORS Origins (parsed): {settings.cors_origins_list}")
    
    print("\n🧪 Testing CORS Origins Parsing...")
    print("-" * 30)
    
    # Test various CORS origin formats
    test_origins = [
        "http://localhost:3000",
        "http://localhost:3000,http://localhost:8080",
        "http://localhost:3000, http://localhost:8080",
        "http://localhost:3000,http://localhost:8080,http://example.com",
        ""
    ]
    
    for test_origin in test_origins:
        try:
            # Simulate the parsing logic
            if not test_origin:
                result = []
            else:
                result = [origin.strip() for origin in test_origin.split(",") if origin.strip()]
            
            print(f"Input: \"{test_origin}\" -> Output: {result}")
        except Exception as e:
            print(f"Input: \"{test_origin}\" -> Error: {e}")
    
    print("\n🎯 Configuration Test Complete!")
    
except ImportError as e:
    print(f"❌ Import Error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Configuration Error: {e}")
    print(f"Error Type: {type(e).__name__}")
    sys.exit(1)

print("\n🚀 Ready to start API Gateway!")
EOF'

echo "✅ Debug script copied to container!"
echo "Run it with: docker-compose exec api_gateway python3 debug_config.py"