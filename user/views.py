from rest_framework import generics, permissions
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from datetime import datetime

from .serializers import UserSerializers
from .models import User, NEW, CODE_VERIFIED


class UserCreate(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializers



class VerifyApiView(APIView):
    permission_classes = (IsAuthenticated, )

    def post(self, request, *args, **kwargs):
        user = self.request.user
        code = self.request.data.get('code')

    
        self.check_verify(user, code)
        return Response(
            data = {
                "success":True,
                "auth_status": user.auth_status,
                "access":user.token()['access'],
                "refresh":user.token()['refresh_token']
            }
        )

    @staticmethod
    def check_verify(user, code):
        verifies = user.verifycode.filter(expiration__gte=datetime.now(), code=code, is_confirmed=False)


        if not verifies.exists():
            data = {
                "message": "Tasdiqlsh kodi xato yoki eskirgan"
            }
            raise ValidationError(data)
        else:
            verifies.update(is_confirmed=True)
        if user.auth_status == NEW:
            user.auth_status = CODE_VERIFIED
            user.save()

        return True

