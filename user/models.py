from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator
from shared.models import BaseModel
from datetime import datetime, timedelta
from rest_framework_simplejwt.tokens import RefreshToken
import random
import uuid



ORDINARY_USER, MANEGER, ADMIN = ('ordinary_user','maneger','admin')
VIA_EMAIL, VIA_PHONE = ('via_email','via_phone')
NEW, CODE_VERIFIED, DONE, PHOTO_DONE = ('new','code_verified','done','photo_done')

PHONE_EXPIRE = 10
EMAIL_EXPIRE = 10

class User(AbstractUser, BaseModel):
    USER_ROLE = (
        (ORDINARY_USER,ORDINARY_USER),
        (MANEGER,MANEGER),
        (ADMIN,ADMIN),
    )
    AUTH_TYPE = (
        (VIA_EMAIL,VIA_EMAIL),
        (VIA_PHONE,VIA_PHONE)
    )
    AUTH_STATUS = (
        (NEW,NEW),
        (CODE_VERIFIED,CODE_VERIFIED),
        (DONE, DONE),
        (PHOTO_DONE,PHOTO_DONE)
    )
    user_roles = models.CharField(max_length=100, choices=USER_ROLE, default=ORDINARY_USER)
    auth_type = models.CharField(max_length=100, choices=AUTH_TYPE)
    auth_status = models.CharField(max_length=100, choices=AUTH_STATUS, default=NEW)
    email = models.EmailField(unique=True,null=True,blank=True)
    phone_number = models.IntegerField(unique=True, null=True,blank=True)
    photo = models.ImageField(upload_to="images/profile/", validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])])

    def create_verify_code(self, verify_type):
        code = "".join([str(random.randint(0,10) % 10) for _ in range(4)])
        UserConfirmation.objects.create(
            user_id = self.id,
            verify_type=verify_type,
            code=code,
        )
        return code
    
    def make_username(self):
        if not self.username:
            temp_username = f'instagram-{uuid.uuid4().__str__().split("-"[-1])}'

            while User.objects.filter(username=temp_username):
                temp_username = f"{temp_username}{random.randint(0,9)}"

            self.username = temp_username

    def make_password(self):
        if not self.password:
            temp_password = f'password-{uuid.uuid4().__str__().split("-"[-1])}'
            self.password = temp_password
    
    def hashing_password(self):
        if not self.password.startswith('pbkdf2_sha256'):
            self.set_password(self.password)

    def check_email(self):
        if self.email:
            oddiy_username = self.email.lower()
            self.email = oddiy_username


    def token(self):
        refresh = RefreshToken.for_user(self)
        return {
            "access": str(refresh.access_token),
            "refresh_token": str(refresh)
        }
    
 
    def save(self, *args, **kwargs):
        self.clean()
        super(User, self).save(*args, **kwargs)

    def clean(self):
        self.check_email()
        self.make_password()
        self.make_username()
        self.hashing_password()
       

    
    


class UserConfirmation(BaseModel):
    AUTH_TYPE = (
        (VIA_EMAIL,VIA_EMAIL),
        (VIA_PHONE,VIA_PHONE)
    )
    verify_type = models.CharField(max_length=255, choices=AUTH_TYPE)
    code = models.CharField(max_length=4)
    user = models.ForeignKey('user.User', on_delete=models.CASCADE, related_name='verifycode')
    expiration = models.DateTimeField(null=True)
    is_confirmed = models.BooleanField(default=False)

    def save(self, *args, **kwargs):

        if self.verify_type == VIA_EMAIL:
            self.expiration = datetime.now() + timedelta(minutes=EMAIL_EXPIRE)
        else:
            self.expiration = datetime.now() + timedelta(minutes=PHONE_EXPIRE)
        super(UserConfirmation, self).save(*args, **kwargs)

 