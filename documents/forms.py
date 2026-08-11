from django import forms
from django.contrib.auth.models import User

from .models import Document, Category
from .utils import generate_reference_number


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = [
            'title', 'reference_number', 'doc_type', 'category',
            'sender', 'receiver', 'description', 'file',
            'status', 'priority', 'date_received', 'due_date', 'assigned_to',
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'የደብዳቤውን ርዕስ ያስገቡ...',
                'autofocus': True,
            }),
            'reference_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'ለምሳሌ: ወ.ከ.አ/001/2019',
            }),
            'doc_type': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'sender': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'ላኪ ስም ወይም ተቋም',
            }),
            'receiver': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'ተቀባይ ስም ወይም ተቋም',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'ስለ ደብዳቤው አጭር መግለጫ ወይም ማስታወሻ...',
            }),
            'file': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png,.gif,.tiff,.bmp,.doc,.docx',
            }),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'date_received': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'due_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['file'].required = False
        self.fields['category'].empty_label = '-- ምድብ ይምረጡ --'
        self.fields['category'].required = False
        self.fields['description'].required = False
        self.fields['date_received'].required = False
        self.fields['due_date'].required = False
        self.fields['assigned_to'].required = False
        self.fields['assigned_to'].queryset = User.objects.filter(is_active=True).order_by('username')
        self.fields['assigned_to'].empty_label = '-- አንድ ሰው ይምረጡ --'
        if not self.instance.pk:
            doc_type = self.initial.get('doc_type') or self.data.get('doc_type') or 'INCOMING'
            self.fields['reference_number'].initial = generate_reference_number(doc_type)

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file and hasattr(file, 'name'):
            ext = file.name.rsplit('.', 1)[-1].lower()
            allowed = ['pdf', 'jpg', 'jpeg', 'png', 'gif', 'tiff', 'bmp', 'doc', 'docx']
            if ext not in allowed:
                raise forms.ValidationError(
                    f'ይህ ፋይል ዓይነት ({ext}) አይፈቀድም። '
                    f'የሚፈቀዱ: {", ".join(allowed)}'
                )
            if file.size > 20 * 1024 * 1024:
                raise forms.ValidationError('ፋይሉ ከ20MB ማለፍ አይችልም።')
        return file


class DocumentSearchForm(forms.Form):
    query = forms.CharField(
        required=False,
        label='',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '🔍  ደብዳቤ ይፈልጉ — ቁጥር፣ ርዕስ፣ ላኪ፣ ተቀባይ...',
            'id': 'search-input',
        }),
    )
    doc_type = forms.ChoiceField(
        required=False,
        label='ዓይነት',
        choices=[('', 'ሁሉም ዓይነቶች')] + Document.DOCUMENT_TYPES,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    status = forms.ChoiceField(
        required=False,
        label='ሁኔታ',
        choices=[('', 'ሁሉም ሁኔታዎች')] + Document.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    priority = forms.ChoiceField(
        required=False,
        label='ቅድሚያ',
        choices=[('', 'ሁሉም ቅድሚያዎች')] + Document.PRIORITY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    category = forms.ModelChoiceField(
        required=False,
        label='ምድብ',
        queryset=Category.objects.all(),
        empty_label='ሁሉም ምድቦች',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    date_from = forms.DateField(
        required=False,
        label='ከቀን',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
    )
    date_to = forms.DateField(
        required=False,
        label='እስከቀን',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
    )


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'amharic_name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Category name in English',
            }),
            'amharic_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'ምድብ ስም በአማርኛ',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'ስለ ምድቡ አጭር መግለጫ...',
            }),
        }
