__author__ = 'mbertrand'


class WorldmapDatabaseRouter(object):
    """A router to control all database operations on models in
    the myapp application"""

    def db_for_read(self, model, **hints):
        "Point all operations on myapp models to 'other'"
        if model._meta.app_label == 'gazetteer':
            return 'wmdata'
        return None

    def db_for_write(self, model, **hints):
        "Point all operations on myapp models to 'other'"
        if model._meta.app_label == 'gazetteer':
            return  'wmdata'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        "Allow any relation if a model in myapp is involved"
        if obj1._meta.app_label == 'gazetteer' or obj2._meta.app_label == 'gazetteer':
            return True
        return None

    def allow_syncdb(self, db, model):
        "Make sure the myapp app only appears on the 'other' db"
        if db == 'wmdata':
            return model._meta.app_label == 'gazetteer'
        elif model._meta.app_label == 'gazetteer':
            return False
        return None

