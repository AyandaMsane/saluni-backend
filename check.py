import os
import sys

print("Python path:", sys.executable)
print("Current directory:", os.getcwd())

try:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    import django
    django.setup()
    
    from api.models import Provider
    print("Provider fields:")
    for f in Provider._meta.get_fields():
        print(f" - {f.name}: {type(f).__name__}")
        
    print("All imports succeeded!")
except Exception as e:
    print("Error:", e)
