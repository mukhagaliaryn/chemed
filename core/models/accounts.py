from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


# User model
class User(AbstractUser):
    USER_TYPE = (
        ('student', _('Студент')),
        ('teacher', _('Оқытушы')),
        ('admin', _('Администрация')),
    )

    USER_CLASS = (
        ('none', _('Сыныпты таңдау')),
        ('8b', _('1-топ')),
        ('8v', _('2-топ')),
    )

    avatar = models.ImageField(_('Сурет'), upload_to='core/account/users/', blank=True, null=True)
    user_type = models.CharField(_('Қолданушы типі'), max_length=32, choices=USER_TYPE, default='student')
    user_class = models.CharField(_('Сыныбы'), max_length=32, choices=USER_CLASS, default='none')

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

    class Meta:
        verbose_name = _('Қолданушы')
        verbose_name_plural = _('Қолданушылар')
