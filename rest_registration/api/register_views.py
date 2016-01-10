from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_registration.notifications import email as notifications_email
from rest_registration.utils import get_user_setting
from rest_registration.settings import settings as registration_settings
from rest_registration.verification import URLParamsSigner
from .serializers import (get_profile_serializer_class,
                          get_register_serializer_class)


class RegisterSigner(URLParamsSigner):

    use_timestamp = True

    @property
    def base_url(self):
        return registration_settings.REGISTER_VERIFICATION_URL

    @property
    def valid_period(self):
        return registration_settings.REGISTER_VERIFICATION_PERIOD


def _register(request):
    serializer_class = get_register_serializer_class()
    serializer = serializer_class(data=request.data)
    serializer.is_valid(raise_exception=True)

    kwargs = {}

    if registration_settings.REGISTER_VERIFICATION_ENABLED:
        verification_flag_field = get_user_setting('VERIFICATION_FLAG_FIELD')
        kwargs[verification_flag_field] = False

    user = serializer.save(**kwargs)

    profile_serializer_class = get_profile_serializer_class()
    profile_serializer = profile_serializer_class(instance=user)
    user_data = profile_serializer.data

    if registration_settings.REGISTER_VERIFICATION_ENABLED:
        signer = RegisterSigner({
            'user_id': user.pk,
        }, request=request)
        email_field = get_user_setting('VERIFICATION_EMAIL_FIELD')
        email = getattr(user, email_field)
        notifications_email.send(email, signer)

    return Response(user_data, status=status.HTTP_201_CREATED)


class RegisterView(APIView):

    def get_serializer_class(self):
        return get_register_serializer_class()

    def post(self, request):
        return _register(request)


register = RegisterView.as_view()
