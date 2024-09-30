# accounts/tasks.py

from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from accounts.models import User
from accounts.utils import account_activation_token

@shared_task
def send_verification_email(user_id):
    try:
        user = User.objects.get(pk=user_id)
        current_site = 'your-domain.com'  # Replace with your domain
        mail_subject = 'Activate your account'
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = account_activation_token.make_token(user)
        activation_link = f'http://{current_site}/api/activate/{uid}/{token}/'

        message = render_to_string('email/activation_email.html', {
            'user': user,
            'activation_link': activation_link,
        })
        send_mail(
            mail_subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
    except User.DoesNotExist:
        pass
