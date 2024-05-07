from rest_framework import serializers
from .models import User, UserConfirmation, VIA_EMAIL, VIA_PHONE
from shared.utils import check_email_or_phone, send_email
from rest_framework.exceptions import ValidationError

class UserSerializers(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)

    def __init__(self, *args, **kwargs):
        super(UserSerializers, self).__init__(*args, **kwargs)
        self.fields['email_phone_number'] =  serializers.CharField(required=False)
       

    class Meta:
        model = User
        fields = (
            'id',
            'auth_type',
            'auth_status'
        )

        extra_kwargs = {
            'auth_type': {'read_only': True, 'required': False},
            'auth_status': {'read_only': True, 'required': False},
            # 'access':{'access': User.token()['access']},
            # 'refresh':{User.token()['refresh_token']},
        }

    def create(self, validation_data):
        user = super(UserSerializers, self).create(validation_data)
        if user.auth_type == VIA_EMAIL:
            code = user.create_verify_code(VIA_EMAIL)
            send_email(user.email, code)
        elif user.auth_type == VIA_PHONE:
            code = user.create_verify_code(VIA_PHONE)
            send_email(user.email, code)

        user.save()
        return user

    def validate(self, data):
        super(UserSerializers, self).validate(data)
        data = self.auth_validate(data)

        return data
    @staticmethod
    def auth_validate(data):
        user_input = str(data.get("email_phone_number")).lower()

        input_type = check_email_or_phone(user_input)

        if input_type == "email":
            data = {
                'email':user_input,
                'auth_type':VIA_EMAIL
            }
        elif input_type == "phone":
            data = {
                'phone':user_input,
                'auth_type':VIA_PHONE
            }
        else:
            data = {
                'status':False,
                'message':"Email yoki telefon xato shekilli"
            }
            raise ValidationError(data)
        return data
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['tokens'] = instance.token()
        return representation



    