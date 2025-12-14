from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Resident, BarangayStaff

class CustomUserUpdateForm(forms.ModelForm):
    class Meta:
        model = Resident
        fields = {
            'first_name',
            'middle_name',
            'last_name',
            'date_of_birth',
            'sex',
            'address',
            'phone_number',
            'civil_status',
            'citizenship',
        }

class CustomUserCreationForm(UserCreationForm):

    class Meta:
        model = CustomUser
        fields = [
            'email',
            'password1',
            'password2',
        ]

    email = forms.EmailField(
        required=True,
        label='Email Address',
        widget=forms.EmailInput(attrs={'placeholder': 'Enter your email'})
    )


    password1 = forms.CharField(
        required=True,
        label='Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter your password'}),
    )

    password2 = forms.CharField(
        required=True,
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm your password'}),
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("This email address is already registered.")
        return email

    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'resident'
        if commit:
            user.save()
        return user

class StaffCreationForm(UserCreationForm):
    """
    Form for creating new staff accounts
    """
    first_name = forms.CharField(
        required=True,
        label='First Name',
        widget=forms.TextInput(attrs={'placeholder': 'Enter first name'}),
        max_length=50
    )
    
    middle_name = forms.CharField(
        required=False,
        label='Middle Name',
        widget=forms.TextInput(attrs={'placeholder': 'Enter middle name (optional)'}),
        max_length=50
    )
    
    last_name = forms.CharField(
        required=True,
        label='Last Name',
        widget=forms.TextInput(attrs={'placeholder': 'Enter last name'}),
        max_length=50
    )
    
    class Meta:
        model = CustomUser
        fields = [
            'email',
            'password1',
            'password2',
        ]

    email = forms.EmailField(
        required=True,
        label='Email Address',
        widget=forms.EmailInput(attrs={'placeholder': 'Enter staff email'})
    )

    password1 = forms.CharField(
        required=True,
        label='Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter password'}),
    )

    password2 = forms.CharField(
        required=True,
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm password'}),
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("This email address is already registered.")
        return email
    
    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        if first_name and not first_name[0].isupper():
            raise forms.ValidationError("First name must start with a capital letter.")
        return first_name
    
    def clean_middle_name(self):
        middle_name = self.cleaned_data.get('middle_name')
        if middle_name and not middle_name[0].isupper():
            raise forms.ValidationError("Middle name must start with a capital letter.")
        return middle_name
    
    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        if last_name and not last_name[0].isupper():
            raise forms.ValidationError("Last name must start with a capital letter.")
        return last_name

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'staff'  # Set role to staff
        if commit:
            user.save()
            # Create BarangayStaff record
            first_name = self.cleaned_data.get('first_name')
            middle_name = self.cleaned_data.get('middle_name')
            last_name = self.cleaned_data.get('last_name')
            BarangayStaff.objects.create(
                user=user,
                first_name=first_name,
                middle_name=middle_name,
                last_name=last_name
            )
        return user

class ResidentForm(forms.ModelForm):
    # Add a separate field for file upload (not bound to the model field)
    address_document_file = forms.FileField(
        required=False,
        label='Upload document (document must show address)',
        widget=forms.FileInput(attrs={
            'accept': 'image/*,application/pdf',
            'class': 'file-input'
        }),
        help_text='Upload a document showing your address (image or PDF)'
    )
    
    class Meta:
        model = Resident
        fields = [
            'first_name',
            'middle_name',
            'last_name',
            'date_of_birth',
            'address',
            'phone_number',
            'sex',
            'civil_status',
            'citizenship',
        ]
    
    first_name = forms.CharField(
        required=True,
        label='First Name',
        widget=forms.TextInput(attrs={'placeholder': 'Enter your first name'})
    )

    last_name = forms.CharField(
        required=True,
        label='Last Name',
        widget=forms.TextInput(attrs={'placeholder': 'Enter your last name'})
    )

    middle_name = forms.CharField(
        required=False,
        label='Middle Name',
        widget=forms.TextInput(attrs={'placeholder': 'Enter your middle name'})
    )

    date_of_birth = forms.DateField(
        required=True,
        label='Date of Birth',
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    address = forms.CharField(
        required=True,
        label='Address',
        widget=forms.TextInput(attrs={'placeholder': 'Enter your address'})
    )

    phone_number = forms.CharField(
        required=False,
        label='Phone Number',
        max_length=11,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter your phone number',
            'maxlength': '11',
            'pattern': '\d{11}',
            'title': 'Phone number must be exactly 11 digits'
        })
    )

    citizenship = forms.CharField(
        required=True,
        label='Citizenship',
        widget=forms.TextInput(attrs={'placeholder': 'Enter your nationality'})
    )

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if phone_number:
            # Check if it's exactly 11 digits
            if not phone_number.isdigit() or len(phone_number) != 11:
                raise forms.ValidationError("Phone number must be exactly 11 digits.")
            if Resident.objects.filter(phone_number=phone_number).exists():
                raise forms.ValidationError("This phone number is already in use.")
        return phone_number

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        if first_name and not first_name[0].isupper():
            raise forms.ValidationError("First name must start with a capital letter.")
        return first_name

    def clean_middle_name(self):
        middle_name = self.cleaned_data.get('middle_name')
        if middle_name and not middle_name[0].isupper():
            raise forms.ValidationError("Middle name must start with a capital letter.")
        return middle_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        if last_name and not last_name[0].isupper():
            raise forms.ValidationError("Last name must start with a capital letter.")
        return last_name

    def clean_citizenship(self):
        citizenship = self.cleaned_data.get('citizenship')
        if citizenship and not citizenship[0].isupper():
            raise forms.ValidationError("Citizenship must start with a capital letter.")
        return citizenship