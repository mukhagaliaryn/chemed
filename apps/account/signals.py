import os
from django.core.files.storage import default_storage
from django.db.models.signals import pre_save, post_delete
from django.dispatch import receiver
from core.models import User


# Manage user avatar signals
# ----------------------------------------------------------------------------------------------------------------------
@receiver(pre_save, sender=User)
def delete_old_avatar(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_avatar = User.objects.get(pk=instance.pk).avatar
            if old_avatar and instance.avatar != old_avatar:
                if default_storage.exists(old_avatar.name):
                    default_storage.delete(old_avatar.name)
        except User.DoesNotExist:
            pass


@receiver(post_delete, sender=User)
def delete_avatar_on_delete(sender, instance, **kwargs):
    if instance.avatar:
        if default_storage.exists(instance.avatar.name):
            default_storage.delete(instance.avatar.name)
