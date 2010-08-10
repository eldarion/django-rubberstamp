from django.db import models
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.generic import GenericForeignKey
from rubberstamp.exceptions import PermissionLookupError


class AppPermissionManager(models.Manager):
    def get_permission_and_content_type(self, permission, obj=None):
        perm_ct = None
        bits = permission.split('.')
        app_label = bits.pop(0)
        if len(bits) >= 3:
            try:
                perm_ct = ContentType.objects.get(app_label=bits[-2], model=bits[-1])
            except ContentType.DoesNotExist:
                codename = '.'.join(bits)
            else:
                codename = '.'.join(bits[:-2])
        else:
            codename = '.'.join(bits)
        
        obj_ct = None
        if obj:
            obj_ct = ContentType.objects.get_for_model(obj)
        
        content_type = perm_ct or obj_ct
        if not (content_type):
            raise PermissionLookupError('ContentType must be given in permission, or object must be passed.')
        if perm_ct and obj_ct and perm_ct != obj_ct:
            raise PermissionLookupError('ContentType in permission and passed object mismatched.')
        
        try:
            return (self.get(
                app_label=app_label,
                content_types=content_type,
                codename=codename
            ), content_type)
        except self.model.DoesNotExist:
            raise PermissionLookupError('AppPermission not found.')
    
    def assign(self, permission, user_or_group, obj=None):
        (perm, ct) = self.get_permission_and_content_type(permission, obj)
        
        assigned_dict = {
            'permission': perm,
            'content_type': ct,
            'object_id': None
        }
        
        if obj:
            assigned_dict['object_id'] = obj.id

        if isinstance(user_or_group, User):
            assigned_dict['user'] = user_or_group
        elif isinstance(user_or_group, Group):
            assigned_dict['group'] = user_or_group
        else:
            raise TypeError('Permissions must be assigned to a User or Group instance.')
        
        return AssignedPermission.objects.get_or_create(**assigned_dict)


class AppPermission(models.Model):
    """
    Permission model which allows apps to add permissions for models in other
    apps, keeping track of the permissions added by each app.
    """
    
    app_label = models.CharField(max_length=100)
    codename = models.CharField(max_length=100)
    description = models.CharField(max_length=100)
    content_types = models.ManyToManyField(ContentType)
    
    objects = AppPermissionManager()
    
    class Meta:
        unique_together = ('app_label', 'codename')
    
    def __unicode__(self):
        return '%s.%s' % (self.app_label, self.codename)


class AssignedPermission(models.Model):
    permission = models.ForeignKey(AppPermission)
    user = models.ForeignKey(User, null=True)
    group = models.ForeignKey(Group, null=True)
    
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField(null=True)
    object = GenericForeignKey()