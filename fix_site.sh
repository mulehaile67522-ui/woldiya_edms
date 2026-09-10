#!/bin/bash
# Run this on PythonAnywhere Bash whenever site breaks
# Usage: bash fix_site.sh

echo "Fixing Woldiya EDMS..."

# Step 1: Fix settings.py
python -c "
content = open('edms_project/settings.py').read()
if 'from decouple' in content or 'ImproperlyConfigured' in content:
    import re
    content = re.sub(r'from decouple.*\n', '', content)
    content = re.sub(r'from django\.core\.exceptions.*\n', '', content)
    content = re.sub(r'.*ImproperlyConfigured.*\n', '', content)
    open('edms_project/settings.py','w').write(content)
    print('settings.py fixed')
else:
    print('settings.py OK')
"

# Step 2: Re-download font if missing
if [ ! -f "static/fonts/ethiopic.ttf" ] || [ $(wc -c < static/fonts/ethiopic.ttf) -lt 50000 ]; then
    echo "Downloading Ethiopic font..."
    python -c "
import urllib.request, os
os.makedirs('static/fonts', exist_ok=True)
urls = [
    'https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSerifEthiopic/NotoSerifEthiopic-Regular.ttf',
]
for url in urls:
    try:
        urllib.request.urlretrieve(url, 'static/fonts/ethiopic.ttf')
        size = os.path.getsize('static/fonts/ethiopic.ttf')
        if size > 50000:
            print('Font OK:', size, 'bytes')
            break
    except Exception as e:
        print('Error:', e)
"
fi

# Step 3: Reload server
touch /var/www/muleedms_pythonanywhere_com_wsgi.py
echo "Site reloaded! Open https://muleedms.pythonanywhere.com"
