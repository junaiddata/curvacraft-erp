from django.contrib.auth.forms import UserCreationForm
from .models import User

class SCOCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email') # We only need these fields from the user