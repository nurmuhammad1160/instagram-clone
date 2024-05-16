from rest_framework import generics, permissions
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from datetime import datetime

from .serializers import UserSerializers, UserChangeSerializer
from .models import User, NEW, CODE_VERIFIED, VIA_EMAIL, VIA_PHONE
from shared.utils import send_email, send_phone


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



class GetNewVerifyCode(APIView):
    permission_classes = [IsAuthenticated, ]


    def get(self, request, *args, **kwargs):
        user = self.request.user
        self.check_verify(user)

        if user.auth_type == VIA_EMAIL:
            code = user.create_verify_code(VIA_EMAIL)
            send_email(user.email, code)
        elif user.auth_type == VIA_PHONE:
            code = user.create_verify_code(VIA_PHONE)
            send_phone(user.phone_number, code)

    @staticmethod
    def check_verify(user):
        verifies = user.verifycode.filter(expiration__gte=datetime.now(), is_confirmed=False)

        if  verifies.exists():
            data = {
                "message": "Sizning kodingiz bilan hali tasdiqlash mumkin! "
            }
            raise  ValidationError(data)
        

class UserChangeInformation(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated, ]
    serializer_class = UserChangeSerializer
    http_method_names = ['put', 'patch']

    def get_object(self):
        return self.request.user


    def update(self, request, *args, **kwargs):
        super(UserChangeInformation, self).update(request, *args, **kwargs)

        data = {
            'message': "User muvofaqiyatli yangilandi! ",
            'auth_status': self.request.user.auth_status
        }
        return Response(data)