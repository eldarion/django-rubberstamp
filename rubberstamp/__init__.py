VERSION = (0, 1, 0, "f", 2) # following PEP 386
DEV_N = 1
POST_N = 1

def get_version():
    version = "%s.%s" % (VERSION[0], VERSION[1])
    if VERSION[2]:
        version = "%s.%s" % (version, VERSION[2])
    if VERSION[3] != "f":
        version = "%s%s%s" % (version, VERSION[3], VERSION[4])
        if DEV_N:
            version = "%s.dev%s" % (version, DEV_N)
    elif POST_N > 0:
        version = "%s.post%s" % (version, POST_N)
    return version


__version__ = get_version()


def autodiscover():
    """
    Auto-discover INSTALLED_APPS permission.py modules, failing silently when
    not present, and create all permissions defined by them if not created
    already.
    """

    from django.conf import settings
    from django.utils.importlib import import_module
    from django.utils.module_loading import module_has_submodule
    
    from django.contrib.contenttypes.models import ContentType
    from rubberstamp.models import AppPermission

    for app in settings.INSTALLED_APPS:
        mod = import_module(app)
        if module_has_submodule(mod, 'permissions'):
            app_label = app.split('.')[-1]
            perm_module = import_module('%s.permissions' % app)
            permissions = getattr(perm_module, 'permissions', [])
            for (codename, description, models) in permissions:
                if not hasattr(models, '__iter__'):
                    models = [models]
                for Model in models:
                    (perm, created) = AppPermission.objects.get_or_create(
                        app_label=app_label,
                        codename=codename,
                        defaults={'description': description},
                    )
                    if perm.description != description:
                        perm.description = description
                        perm.save()
                    perm.content_types.add(ContentType.objects.get_for_model(Model))
