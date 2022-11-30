from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import CreationForm


class SignUp(CreateView):
    template_name = 'users/signup.html'
    form_class = CreationForm
    success_url = reverse_lazy('posts:index')
