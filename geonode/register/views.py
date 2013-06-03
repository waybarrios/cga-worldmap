from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth import login
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.models import User
from geonode.account.forms import UserRegistrationForm, ForgotUsernameForm
from django.core.mail import send_mail
from django.utils.translation import ugettext as _
import logging
import account.views
from account.utils import default_redirect
from django.contrib.sites.models import Site
from geonode.profile.models import WorldmapProfile
import Cookie, os
logger = logging.getLogger("geonode.account.views")


class SignupView(account.views.SignupView):

    form_class = UserRegistrationForm

    def get_success_url(self, fallback_url=None, **kwargs):
        if fallback_url is None:
            new_user = self.created_user
            if new_user.get_profile().is_org_member:
                self.request.session["group_username"] = new_user.username
                logger.debug("group username set to [%s]", new_user.username)
                return settings.CUSTOM_ORG_AUTH_URL
            elif "bra_harvard_redirect" in self.request.session:
                new_user.active = True
                new_user.save()
                new_user.backend = 'django.contrib.auth.backends.ModelBackend'
                # This login function does not need password.
                login(self.request, new_user)
                fallback_url = self.request.session["bra_harvard_redirect"]
            else:
                fallback_url = settings.ACCOUNT_SIGNUP_REDIRECT_URL
        kwargs.setdefault("redirect_field_name", self.get_redirect_field_name())
        return default_redirect(self.request, fallback_url, **kwargs)

    def after_signup(self, form):
        self.create_profile(form)
        super(SignupView, self).after_signup(form)
        #super(SignupView, self).after_signup(form)

    def create_profile(self, form):
        profile = self.created_user.get_profile()
        profile.is_org_member = form.cleaned_data["is_org_member"]
        profile.member_expiration_dt = datetime.today()
        profile.save()


def forgotUsername(request,template_name='register/username_form.html'):

    username_form = ForgotUsernameForm()
    message = ''


    #email_subject = _("Your username for ") + Site.objects.get_current().current_site.name
    email_subject = _("Your username for ") + settings.SITENAME

    if request.method == 'POST':
        username_form = ForgotUsernameForm(request.POST)
        if username_form.is_valid():

            users = User.objects.filter(email=username_form.cleaned_data['email'])
            if len(users) > 0:
                username = users[0].username
                email_message = email_subject + " : " + username
                send_mail(email_subject, email_message, settings.DEFAULT_FROM_EMAIL,
                    [username_form.cleaned_data['email']], fail_silently=False)
                message = _("Your username has been emailed to you.")
            else:
                message = _("No user could be found with that email address.")


    return render_to_response(template_name, RequestContext(request, {
        'message': message,
        'form' : username_form
        }))



def confirm(request):
    if request.user and settings.CUSTOM_ORG_AUTH_URL is not None:
        request.session["group_username"] = request.user.username
        logger.debug("group username set to [%s]", request.user.username)
        return HttpResponseRedirect(settings.CUSTOM_ORG_AUTH_URL)
    else:
        return HttpResponseRedirect("/")



def registercompleteOrganizationUser(request, template_name='register/registration_complete.html',):
    if "group_username" in request.session and settings.CUSTOM_ORG_COOKIE in request.COOKIES:
        username = request.session["group_username"]
        user = User.objects.get(username=username)
        userProfile = user.get_profile()
        if user:
            userProfile.is_org_member = True
            userProfile.member_expiration_dt = datetime.today() + timedelta(days=365)
            userProfile.save()
            del request.session["group_username"]
            #else:
            #    userProfile.is_org_member = False
            #    userProfile.save()
            if "bra_harvard_redirect" in request.session:
                user.active = True
                user.save()
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                # This login function does not need password.
                login(request, user)
                return HttpResponseRedirect(request.session["bra_harvard_redirect"])

            if user.is_active:
                return HttpResponseRedirect(user.get_profile().get_absolute_url())
    else:
        logger.debug("harvard username is not found")
        if request.user and  request.user.is_active:
                return HttpResponseRedirect(request.user.get_profile().get_absolute_url())

    return render_to_response(template_name, RequestContext(request))
    
    
    
    
    
    
    
    
    
