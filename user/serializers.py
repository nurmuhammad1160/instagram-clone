from rest_framework import serializers
from .models import User, UserConfirmation, VIA_EMAIL, VIA_PHONE, NEW, CODE_VERIFIED, DONE
from shared.utils import check_email_or_phone, send_email, send_phone
from rest_framework.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password

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
            'auth_status': {'read_only': True, 'required': False}
        }

    def create(self, validation_data):
        user = super(UserSerializers, self).create(validation_data)
        if user.auth_type == VIA_EMAIL:
            code = user.create_verify_code(VIA_EMAIL)
            send_email(user.email, code)
        elif user.auth_type == VIA_PHONE:
            code = user.create_verify_code(VIA_PHONE)
            send_phone(user.phone_number, code)

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


class UserChangeSerializer(serializers.Serializer):
    first_name = serializers.CharField(write_only=True, max_length=200, required=True)
    last_name = serializers.CharField(write_only=True, max_length=200, required=True)
    username = serializers.CharField(write_only=True, required=True)
    password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)

    def validate(self, data):
        password = data.get('password')
        confirm_password = data.get('confirm_password')

        if password != confirm_password:
            raise ValidationError(
                {
                    'message': 'Parol mos tushmayapdi!'
                }
            )
        if password:
            validate_password(password)
            validate_password(confirm_password)

        return data
    def validate_first_name(self, first_name):
        if len(first_name) < 3 or len(first_name) > 30:
            data = {
                'message': "Ism 3 tadan ko'proq va 30 tadan kamroq belgidan iborat bo'lishi kerak! "
            }

            raise ValidationError(data)
        if first_name.isdigit():
            data = {
                "messege":"Ism faqatgina raqamlardan iborat bo'lishi mumkin emas!"
            }
            raise ValidationError(data)
        
        return first_name

    def update(self, instance, validated_data):
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.username = validated_data.get('username', instance.username)
        instance.password = validated_data.get('password', instance.password)

        if validated_data.get('password'):
            instance.set_password(validated_data.get('password'))
        if instance.auth_status == CODE_VERIFIED:
            instance.auth_status = DONE
        instance.save()

        return instance