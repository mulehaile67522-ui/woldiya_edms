"""
Seed all Woldiya City Administration departments and sub-cities.
Run: python seed_departments.py
"""
import os, django
os.environ['DJANGO_SETTINGS_MODULE'] = 'edms_project.settings'
django.setup()

from documents.models import Department

# ── City Level (ከተማ አስተዳደር ደረጃ) ──────────────────────────────────
CITY_LEVEL = [
    ('ከንቲባ ጽፈት ቤት',                'Mayor Office',         1),
    ('ምክር ቤት ጽፈት ቤት',              'Council Office',        2),
]

# ── Departments under Mayor (ከንቲባ ስር) ─────────────────────────────
DEPARTMENTS = [
    # (name, short_name, order)
    ('ገቢዎች ጽፈት ቤት',                'ገቢዎች',                 10),
    ('ገንዘብ መምሪያ',                   'ፋይናንስ',                11),
    ('ሴቶችና ህጻናት መምሪያ',             'ሴቶች/ህጻናት',             12),
    ('ንግድና ገበያ ልማት መምሪያ',          'ንግድ',                   13),
    ('ምግብ ዋስትና ተጠሪ ጽፈት ቤት',        'ምግብ ዋስትና',             14),
    ('ሲቪል ሰርቪስ መምሪያ',              'ሲቪል ሰርቪስ',             15),
    ('ጤና መምሪያ',                     'ጤና',                    16),
    ('ኮሙኒኬሽን መምሪያ',                 'ኮሙኒኬሽን',               17),
    ('ስራ እና ክህሎት መምሪያ',            'ስራ/ክህሎት',              18),
    ('ትምህርት መምሪያ',                  'ትምህርት',                 19),
    ('ባህልና ቱሪዝም ስፖርት መምሪያ',        'ባህል/ቱሪዝም',             20),
    ('ትራንስፖርት ሎጅስቲክ መምሪያ',        'ትራንስፖርት',              21),
    ('ማህበራት ተጠሪ ጽፈት ቤት',          'ማህበራት',                22),
    ('እንሣትና አሳ ሃብት መምሪያ',          'እንሣት/አሳ',              23),
    ('ግብርና መምሪያ',                   'ግብርና',                  24),
    ('መሰረተ ልማት መምሪያ',              'መሰረተ ልማት',             25),
    ('መሬት መምሪያ',                    'መሬት',                   26),
    ('ፍትህ ተጠሪ ጽፈት ቤት',             'ፍትህ',                   27),
    ('ፖሊስ መምሪያ',                    'ፖሊስ',                   28),
    ('ጸጥታ ተጠሪ ጽፈት ቤት',            'ጸጥታ',                   29),
    ('ሚኒሻ ተጠሪ ጽፈት ቤት',            'ሚኒሻ',                   30),
    ('ፈጠራ እና ቴክኖሎጂ ቡድን',          'IT/ፈጠራ',               31),
    ('ሌሎች',                          'ሌሎች',                   99),
]

# ── Sub-cities (ክፍለ ከተሞች) ────────────────────────────────────────
SUBCITIES = [
    ('ታላቁ ራሳሊ ክፍለ ከተማ ጽፈት ቤት',   'ራሳሊ',                   50),
    ('የጁ ክፍለ ከተማ ጽፈት ቤት',          'የጁ',                    51),
    ('ጣይቱ ክፍለ ከተማ ጽፈት ቤት',         'ጣይቱ',                   52),
]

created = 0
skipped = 0

# City level
for name, short, order in CITY_LEVEL:
    obj, new = Department.objects.get_or_create(
        name=name,
        defaults={'short_name': short, 'level': 'CITY', 'order': order}
    )
    if new:
        created += 1
        print(f'  ✓ {name}')
    else:
        skipped += 1

# Departments
for name, short, order in DEPARTMENTS:
    obj, new = Department.objects.get_or_create(
        name=name,
        defaults={'short_name': short, 'level': 'DEPT', 'order': order}
    )
    if new:
        created += 1
        print(f'  ✓ {name}')
    else:
        skipped += 1

# Sub-cities
for name, short, order in SUBCITIES:
    obj, new = Department.objects.get_or_create(
        name=name,
        defaults={'short_name': short, 'level': 'SUBCITY', 'order': order}
    )
    if new:
        created += 1
        print(f'  ✓ {name}')
    else:
        skipped += 1

print(f'\n✅ {created} ቢሮዎች/መምሪያዎች ተፈጠሩ | {skipped} ነበሩ')
print(f'ጠቅላላ: {Department.objects.count()} ቢሮዎች')
