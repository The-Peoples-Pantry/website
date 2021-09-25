from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from volunteers.models import Volunteer


class UserCreationForm(forms.ModelForm):
    """
    A modified version of the official UserCreationForm, that requests and email
    and sets the username to match. Creates a user, with no privileges.
    """

    error_messages = {
        "password_mismatch": "The two password fields didn’t match.",
        "already_registered": "There is already an account registered with that email",
    }

    password1 = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        help_text=password_validation.password_validators_help_text_html(),
    )

    password2 = forms.CharField(
        label="Password confirmation",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        strip=False,
        help_text="Enter the same password as before, for verification.",
    )

    class Meta:
        model = User
        fields = ("email",)
        field_classes = {"email": forms.EmailField}
        widgets = {
            "email": forms.EmailInput(
                attrs={
                    "autocomplete": "email",
                    "autofocus": True,
                }
            )
        }

    def clean_email(self):
        # Validate the email for uniqueness
        # Django's user model does not apply a unique constraint on the DB field
        # so we need to perform a manual validation here
        email = self.cleaned_data.get("email")
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError(
                self.error_messages["already_registered"],
                code="already_registered",
            )
        return email

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError(
                self.error_messages["password_mismatch"],
                code="password_mismatch",
            )
        return password2

    def _post_clean(self):
        super()._post_clean()
        # Validate the password after self.instance is updated with form data
        # by super().
        password = self.cleaned_data.get("password2")
        if password:
            try:
                password_validation.validate_password(password, self.instance)
            except ValidationError as error:
                self.add_error("password2", error)

    def save(self, commit=True):
        # Set the password on the user and set the email as the username
        user = super().save(commit=False)
        user.username = user.email
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class VolunteerProfileForm(forms.ModelForm):
    class Meta:
        model = Volunteer
        fields = [
            "name",
            "short_name",
            "phone_number",
            "address_1",
            "address_2",
            "pronouns",
            "notes",
            "postal_code",
            "city",
        ]


class DateInput(forms.DateInput):
    input_type = "date"


class DateField(forms.DateField):
    widget = DateInput
