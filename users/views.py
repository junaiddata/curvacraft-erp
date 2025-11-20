# users/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import SCOCreationForm

@login_required
def sco_add_popup(request):
    if request.method == 'POST':
        form = SCOCreationForm(request.POST)
        if form.is_valid():
            new_user = form.save(commit=False)
            new_user.role = 'sco'  # CRITICAL: Set the role automatically
            new_user.save()
            
            # This is the magic: respond with JS that calls a function in the parent window
            return render(request, 'users/popup_response.html', {
                'pk_value': new_user.pk,
                'str_value': new_user.username
            })
    else:
        form = SCOCreationForm()

    return render(request, 'users/sco_add_popup.html', {'form': form})