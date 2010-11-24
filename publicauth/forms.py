from django.utils.translation import ugettext as _
from django.contrib.auth.models import User
from django import forms

from publicauth.models import PublicID
from publicauth import settings


class ExtraForm(forms.Form):

    username = forms.CharField(min_length=3, max_length=25, label="Display Name")

    def clean_username(self):
        try:
            User.objects.get( username = self.cleaned_data[ 'username' ] )
            raise forms.ValidationError(_(u'This username name is already taken'))
        except User.DoesNotExist:
            return self.cleaned_data['username']

    def save(self, request, identity, provider):
        user = User.objects.create(username=self.cleaned_data['username'])
        if settings.PUBLICAUTH_ACTIVATION_REQUIRED:
            user.is_active = False
        user.save()
        PublicID.objects.create(user=user, identity=identity, provider=provider)
        return user
