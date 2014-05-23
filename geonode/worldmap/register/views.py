
import account
from datetime import datetime, timedelta
from account.utils import default_redirect
from django.conf import settings
from django.contrib.auth import login
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.models import User
from geonode.worldmap.register.forms import UserRegistrationForm, ForgotUsernameForm
from django.core.mail import send_mail
from django.utils.translation import ugettext as _
from django.contrib.sites.models import Site
from geonode.people.models import Profile
import re
import logging

logger = logging.getLogger("geonode.worldmap.register.views")

class SignupView(account.views.SignupView):

    form_class = UserRegistrationForm

    def get_success_url(self, fallback_url=None, **kwargs):
        if fallback_url is None:
            new_user = self.created_user
            if new_user.get_profile().is_org_member:
                self.request.session["group_username"] = new_user.username
                logger.debug("group username set to [%s]", new_user.username)
                return settings.CUSTOM_AUTH["auth_url"]
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
        if settings.CUSTOM_AUTH["enabled"]:
            profile.is_org_member = form.cleaned_data["is_org_member"]
        profile.member_expiration_dt = datetime.today()
        profile.save()


def forgotUsername(request,template_name='register/username_form.html'):

    username_form = ForgotUsernameForm()
    message = ''


    email_subject = _("Your username for ") + Site.objects.get_current().name

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
    if request.user and settings.CUSTOM_AUTH["auth_url"] is not None:
        request.session["group_username"] = request.user.username
        logger.debug("group username set to [%s]", request.user.username)
        return HttpResponseRedirect(settings.CUSTOM_AUTH["auth_url"])
    else:
        return HttpResponseRedirect("/")


# def registerOrganizationUser(request, success_url=None,
#              form_class=UserRegistrationForm, profile_callback=None,
#              template_name='registration/registration_form.html',
#              extra_context=None):
#
#     if request.method == 'POST':
#         form = form_class(data=request.POST, files=request.FILES)
#         if form.is_valid():
#             new_user = form.save(profile_callback=profile_callback)
#             # success_url needs to be dynamically generated here; setting a
#             # a default value using reverse() will cause circular-import
#             # problems with the default URLConf for this application, which
#             # imports this file.
#
#
#             if new_user.get_profile().is_org_member:
#                 request.session["group_username"] = new_user.username
#                 logger.debug("group username set to [%s]", new_user.username)
#                 return HttpResponseRedirect(settings.CUSTOM_AUTH["auth_url"])
#             elif "bra_harvard_redirect" in request.session:
#                 new_user.active = True
#                 new_user.save()
#                 new_user.backend = 'django.contrib.auth.backends.ModelBackend'
#                 # This login function does not need password.
#                 login(request, new_user)
#                 return HttpResponseRedirect(request.session["bra_harvard_redirect"])
#             else:
#                 return HttpResponseRedirect(success_url or reverse('registration_complete'))
#     else:
#         form = form_class()
#
#     if extra_context is None:
#         extra_context = {}
#     context = RequestContext(request)
#     for key, value in extra_context.items():
#         context[key] = callable(value) and value() or value
#     return render_to_response(template_name,
#                               { 'form': form },
#                               context_instance=context)# Create your views here.


def registercompleteOrganizationUser(request, template_name='registration/registration_complete.html',):
    if "group_username" in request.session:
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

def forgot_username(request):
    """ Look up a username based on an email address, and send an email
    containing the username if found"""

    username_form = ForgotUsernameForm()

    message = ''

    site = Site.objects.get_current()

    email_subject = _("Your username for " + site.name)

    if request.method == 'POST':
        username_form = ForgotUsernameForm(request.POST)
        if username_form.is_valid():

            users = User.objects.filter(
                email=username_form.cleaned_data['email'])
            if len(users) > 0:
                username = users[0].username
                email_message = email_subject + " : " + username
                send_mail(email_subject, email_message,
                          settings.DEFAULT_FROM_EMAIL,
                          [username_form.cleaned_data['email']],
                          fail_silently=False)
                message = _("Your username has been emailed to you.")
            else:
                message = _("No user could be found with that email address.")

    return render_to_response('account/forgot_username_form.html',
                              RequestContext(request, {
                                  'message': message,
                                  'form': username_form
                              }))

def _create_new_user(user_email, map_layer_title, map_layer_url, map_layer_owner_id):
    random_password = User.objects.make_random_password()
    user_name = re.sub(r'\W', r'', user_email.split('@')[0])
    user_length = len(user_name)
    if user_length > 30:
        user_name = user_name[0:29]
    while len(User.objects.filter(username=user_name)) > 0:
        username = user_name[0:user_length-4] + User.objects.make_random_password(length=4, allowed_chars='0123456789')
    email = user_email.strip()
    new_user = User(username=username,email=email)
    new_user.set_password(User.objects.make_random_password(length=4, allowed_chars='0123456789'))
    new_user.is_active = False
    new_user.save()
    if new_user:
        new_profile = Profile.objects.get_or_create(user=new_user, name=new_user.username, email=new_user.email)
        if settings.CUSTOM_AUTH["enabled"] and new_user.email.endswith(settings.CUSTOM_AUTH["email_suffix"]):
            new_profile.is_org_member = True
            new_profile.member_expiration_dt = datetime.today() + timedelta(days=365)
            new_profile.save()
    try:
        _send_permissions_email(user_email, map_layer_title, map_layer_url, map_layer_owner_id, random_password)
    except:
        logger.debug("An error ocurred when sending the mail")
    return new_user



def _send_permissions_email(user_email, map_layer_title, map_layer_url, map_layer_owner_id,  password):

    current_site = Site.objects.get_current()
    user = User.objects.get(email = user_email)
    profile = Profile.objects.get(user=user)
    owner = User.objects.get(id=map_layer_owner_id)

    subject = render_to_string('register/new_user_email_subject.txt',
            { 'site': current_site,
              'owner' : (owner.get_profile().name if owner.get_profile().name else owner.email),
              })
    # Email subject *must not* contain newlines
    subject = ''.join(subject.splitlines())

    message = render_to_string('register/new_user_email.txt',
            { 'activation_key': profile.activation_key,
              'expiration_days': settings.ACCOUNT_ACTIVATION_DAYS,
              'owner': (owner.get_profile().name if owner.get_profile().name else owner.email),
              'title': map_layer_title,
              'url' : map_layer_url,
              'site': current_site,
              'username': user.username,
              'password' : password })

    send_mail(subject, message, settings.NO_REPLY_EMAIL, [user.email])


