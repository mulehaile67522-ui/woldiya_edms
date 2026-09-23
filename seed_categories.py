"""
Run once to seed standard Woldiya City Administration document categories.
python seed_categories.py
"""
import os, django
os.environ['DJANGO_SETTINGS_MODULE'] = 'edms_project.settings'
django.setup()

from documents.models import Category

CATEGORIES = [
    # (name_en,             amharic_name,                   description)
    ('Administrative',      'አስተዳደር',                      'አጠቃላይ አስተዳደር ነክ ደብዳቤዎች እና ሰነዶች'),
    ('Finance',             'ፋይናንስ',                       'ፋይናንሻዊ ሪፖርቶች፣ ግዥ፣ ክፍያ እና በጀት ነክ ሰነዶች'),
    ('Human Resources',     'ሰው ሃብት',                      'የሠራተኞች ቅጥር፣ ዝውውር፣ ዕረፍት እና ጡረታ'),
    ('Legal',               'ህጋዊ ጉዳዮች',                    'ውሎች፣ ስምምነቶች፣ ደንቦች እና ሕጋዊ ደብዳቤዎች'),
    ('Planning',            'ዕቅድ እና ፕሮግራም',               'ዓመታዊ ዕቅዶች፣ ሪፖርቶች እና ፕሮጀክቶች'),
    ('Infrastructure',      'መሠረተ ልማት',                    'ግንባታ፣ መንገድ፣ ውሃ እና የልማት ፕሮጀክቶች'),
    ('Health',              'ጤና',                           'የጤና አገልግሎት ነክ ደብዳቤዎች እና ሪፖርቶች'),
    ('Education',           'ትምህርት',                        'ትምህርት ቤቶች፣ ሥልጠና እና የትምህርት ፖሊሲ'),
    ('Land & Property',     'መሬት እና ንብረት',                  'የመሬት ምዝገባ፣ ፈቃዶች እና ንብረት ነክ ጉዳዮች'),
    ('Revenue',             'ገቢ',                           'ግብር፣ ፈቃድ እና ሌሎች ከተማ ገቢ ነክ ጉዳዮች'),
    ('Security',            'ፀጥታ',                          'ፀጥታ፣ ፖሊስ እና ሕዝብ ደህንነት ነክ ጉዳዮች'),
    ('Public Relations',    'ሕዝብ ግንኙነት',                   'ለሕዝብ ማሳወቂያ፣ ሚዲያ እና ህዝባዊ ዝግጅቶች'),
    ('Social Affairs',      'ማህበራዊ ጉዳዮች',                  'ማህበራዊ ጥበቃ፣ ሴቶችና ሕጻናት ነክ ጉዳዮች'),
    ('Agriculture',         'ግብርና',                         'የግብርና ድጋፍ፣ ምርት እና ዕፅዋት ጥበቃ'),
    ('Trade & Industry',    'ንግድ እና ኢንዱስትሪ',               'ፈቃዶች፣ ቁጥጥር እና ኢንዱስትሪ ልማት'),
    ('IT & Innovation',     'ቴክኖሎጂ እና ፈጠራ',               'ዲጂታል አገልግሎቶች፣ ፈጠራ እና ቴክኖሎጂ'),
    ('Procurement',         'ግዥ',                           'አቅርቦት፣ ጨረታ እና ኮንትራት ሰነዶች'),
    ('Meeting Minutes',     'የስብሰባ ቃለ ጉባኤ',                'የሥራ አስፈጻሚ ስብሰባ፣ ቦርድ እና ኮሚቴ ጉባኤ'),
    ('Complaints',          'አቤቱታ እና ቅሬታ',                 'ከዜጎች የቀረቡ አቤቱታዎች እና ምላሾቻቸው'),
    ('Other',               'ሌላ',                           'ከላይ ባሉ ምድቦች ያልተሸፈኑ ደብዳቤዎች'),
]

created = 0
skipped = 0
for name, amharic, desc in CATEGORIES:
    obj, new = Category.objects.get_or_create(
        name=name,
        defaults={'amharic_name': amharic, 'description': desc}
    )
    if new:
        created += 1
        print(f"  ✓ ተፈጠረ: {amharic} ({name})")
    else:
        skipped += 1
        print(f"  — ነበር:  {amharic} ({name})")

print(f"\n✅ {created} ምድቦች ተፈጠሩ  |  {skipped} ነበሩ")
