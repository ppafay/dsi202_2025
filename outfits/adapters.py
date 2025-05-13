# outfits/adapters.py

from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.utils.text import slugify
from django.contrib.auth.models import User
import random
import string


class ForceAutoSignupAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)

        # 👇 ป้องกัน username ซ้ำ โดยเติมตัวเลขท้าย slug ชื่อ
        base_username = slugify(data.get("name") or data.get("email").split("@")[0])
        username = base_username
        counter = 0

        while User.objects.filter(username=username).exists():
            counter += 1
            username = f"{base_username}{counter}"

        user.username = username
        return user
