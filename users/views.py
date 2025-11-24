# users/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import SCOCreationForm
from .models import User # Make sure User is imported
from users.decorators import admin_required # Import our admin decorator

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


# --- ADD THIS NEW VIEW for the list page ---
@login_required
@admin_required
def manage_scos_list(request):
    # Get all users with the role of 'sco', order by their active status then username
    all_scos = User.objects.filter(role='sco').order_by('-is_active', 'username')
    context = {'scos': all_scos}
    return render(request, 'users/manage_scos.html', context)

# --- ADD THIS NEW VIEW for the toggle action ---
@login_required
@admin_required
def toggle_sco_status(request, user_pk):
    # Ensure this is a POST request for security
    if request.method == 'POST':
        sco_to_toggle = get_object_or_404(User, pk=user_pk, role='sco')
        # Flip the boolean status
        sco_to_toggle.is_active = not sco_to_toggle.is_active
        sco_to_toggle.save()
        
        status = "activated" if sco_to_toggle.is_active else "deactivated"
        messages.success(request, f"User '{sco_to_toggle.username}' has been {status}.")
    
    # Redirect back to the list page regardless of method
    return redirect('users:manage_scos')