# 🏛️ ወልድያ ከተማ አስተዳደር — የሰነድ አስተዳደር ስርዓት (EDMS)

**Woldiya City Administration Electronic Document Management System**

A comprehensive Django-based document management system with bilingual (Amharic/English) interface, built for managing incoming, outgoing, and internal documents with full workflow tracking.

---

## 🚀 Quick Start

### Option 1: Double-click to start
Simply double-click `START_SERVER.bat` to start the server.

### Option 2: Command line
```batch
cd C:\Users\muleh\OneDrive\Desktop\woldiya-emds\woldiya_edms
venv\Scripts\activate
python manage.py runserver
```

Then open your browser to:
- **Main App**: http://127.0.0.1:8000
- **Admin Panel**: http://127.0.0.1:8000/admin/

---

## 🔐 Default Login

| Field | Value |
|-------|-------|
| Username | `admin` |
| Password | `admin1234` |

---

## ✨ Features

### Document Management
- ✅ **Full CRUD**: Create, Read, Update, Delete documents
- 📁 **Document Types**: Incoming (ገቢ), Outgoing (ወጪ), Internal (የውስጥ)
- 🏷️ **Categories**: Organize documents by custom categories
- 📎 **File Attachments**: PDF and image support with inline preview
- 🔍 **Advanced Search**: Multi-field search with filters
- 📊 **Dashboard**: Real-time statistics and recent activity
- 📄 **Pagination**: Efficient browsing of large document collections

### Workflow Features
- 🔄 **Status Tracking**: Pending, In Progress, Completed, Archived
- ⚡ **Priority Levels**: Low, Medium, High, Urgent
- 📅 **Date Management**: Received date, Due date tracking
- 👤 **User Attribution**: Tracks who created each document
- 🔔 **Overdue Alerts**: Dashboard highlights overdue documents

### User Interface
- 🌐 **Bilingual**: Amharic & English
- 🎨 **Modern UI**: Bootstrap 5 with custom Ethiopian branding
- 📱 **Responsive**: Works on desktop, tablet, and mobile
- 🎯 **Intuitive Navigation**: Sidebar with organized menu
- 📊 **Rich Dashboard**: Statistics cards and recent activity

### Admin Panel
- ⚙️ **Enhanced Admin**: Searchable, filterable document lists
- 🔎 **Search Fields**: Reference number, title, sender, receiver
- 📋 **List Filters**: Type, status, priority, category, date
- 📁 **Fieldsets**: Organized form sections
- 📅 **Date Hierarchy**: Browse by creation date

---

## 📂 Project Structure

```
woldiya_edms/
├── documents/               # Main app
│   ├── migrations/         # Database migrations
│   ├── admin.py           # Admin configuration
│   ├── forms.py           # Form definitions
│   ├── models.py          # Data models (Document, Category)
│   ├── views.py           # View logic
│   └── urls.py            # URL routing
├── edms_project/          # Project settings
│   ├── settings.py        # Django settings
│   └── urls.py            # Root URL config
├── templates/             # HTML templates
│   ├── base.html         # Base template with sidebar
│   └── documents/        # Document templates
│       ├── dashboard.html
│       ├── document_list.html
│       ├── document_detail.html
│       ├── document_form.html
│       ├── document_confirm_delete.html
│       └── login.html
├── media/                 # Uploaded files (auto-created)
│   └── documents/        # Document files organized by year/month
├── static/               # Static files (CSS, JS)
├── db.sqlite3            # SQLite database
├── manage.py             # Django management script
└── START_SERVER.bat      # Quick start script
```

---

## 📊 Database Models

### Document Model
```python
- title                 # Document title
- reference_number      # Unique document ID
- doc_type             # INCOMING / OUTGOING / INTERNAL
- category             # ForeignKey to Category (optional)
- sender               # Sender name/department
- receiver             # Receiver name/department
- description          # Additional notes
- file                 # PDF/Image attachment
- status               # PENDING / IN_PROGRESS / COMPLETED / ARCHIVED
- priority             # LOW / MEDIUM / HIGH / URGENT
- date_received        # When document was received
- due_date            # Deadline
- created_at          # Auto timestamp
- updated_at          # Auto timestamp
- created_by          # ForeignKey to User
```

### Category Model
```python
- name                # English name
- amharic_name        # Amharic name
- description         # Category description
- created_at          # Auto timestamp
```

---

## 🛠️ Management Commands

### Create superuser
```bash
python manage.py createsuperuser
```

### Run migrations
```bash
python manage.py migrate
```

### Create new migration (after model changes)
```bash
python manage.py makemigrations
```

### Run server
```bash
python manage.py runserver
# Or specify port
python manage.py runserver 8080
```

### System check
```bash
python manage.py check
```

### Collect static files (for production)
```bash
python manage.py collectstatic
```

---

## 📦 Dependencies

All dependencies are already installed in the virtual environment (`venv/`):

- Django 6.0.7
- Python 3.x
- SQLite (built-in)
- Bootstrap 5 (CDN)
- Bootstrap Icons (CDN)

---

## 🔧 Configuration

### Settings Location
`edms_project/settings.py`

### Key Settings
- `DEBUG = True` - Development mode (set to False for production)
- `ALLOWED_HOSTS = ['*']` - Allow all hosts (restrict for production)
- `TIME_ZONE = 'Africa/Addis_Ababa'` - Ethiopian timezone
- `LANGUAGE_CODE = 'am'` - Amharic language code
- `MEDIA_ROOT` - Files stored in `media/` folder
- `STATIC_ROOT` - Static files in `staticfiles/` folder

---

## 📝 Usage Guide

### Adding a New Document
1. Click **"አዲስ ምዝገባ"** (New Registration) in sidebar or dashboard
2. Fill in required fields:
   - Reference Number (e.g., 001/2017)
   - Title
   - Document Type
   - Sender & Receiver
   - Upload file (PDF or image)
3. Optionally set:
   - Category
   - Status & Priority
   - Dates
   - Description
4. Click **"ምዝገባ"** (Register) to save

### Searching Documents
1. Go to **"ሁሉም ደብዳቤዎች"** (All Documents)
2. Use search filters:
   - Text search (searches title, ref number, sender, receiver)
   - Filter by type, status, priority
   - Filter by date range
3. Click search icon 🔍
4. Click ❌ to clear filters

### Viewing Document Details
1. Click on any reference number or **👁️ view** button
2. See all document metadata
3. Preview PDF inline or download
4. Edit or delete from this page

### Admin Panel
1. Go to http://127.0.0.1:8000/admin/
2. Login with admin credentials
3. Manage:
   - Documents (with advanced search/filter)
   - Categories
   - Users
   - Groups

---

## 🎨 UI Customization

### Colors
Edit CSS variables in `templates/base.html`:
```css
:root {
  --primary:   #1a5276;  /* Main brand color */
  --secondary: #2e86c1;  /* Secondary color */
  --accent:    #f39c12;  /* Accent color */
}
```

### Logo
Replace the emoji 🏛️ in `base.html` with your logo:
```html
<div class="sidebar-brand">
  <img src="{% static 'logo.png' %}" alt="Logo" />
</div>
```

---

## 🐛 Troubleshooting

### Port already in use
```bash
python manage.py runserver 8080
```

### Database locked
Close any DB browser tools and restart server.

### File upload errors
Check `media/` folder permissions.

### Missing migrations
```bash
python manage.py migrate
```

### Static files not loading
```bash
python manage.py collectstatic --noinput
```

---

## 📈 Future Enhancements

Potential features to add:
- [ ] Email notifications
- [ ] Document version history
- [ ] Advanced permissions per department
- [ ] Digital signatures
- [ ] Mobile app
- [ ] Report generation (PDF export)
- [ ] Document workflow approval chains
- [ ] Full-text search with Elasticsearch
- [ ] Multi-language switching
- [ ] Backup/restore functionality

---

## 👨‍💻 Development

### Adding new fields to Document
1. Edit `documents/models.py`
2. Run: `python manage.py makemigrations`
3. Run: `python manage.py migrate`
4. Update forms, templates as needed

### Creating new views
1. Add function to `documents/views.py`
2. Add URL pattern in `documents/urls.py`
3. Create template in `templates/documents/`

---

## 📜 License

Internal city administration project. All rights reserved.

---

## 📞 Support

For issues or questions, contact the IT department at Woldiya City Administration.

---

**Built with ❤️ for ወልድያ ከተማ አስተዳደር**
