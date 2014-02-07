from celery.schedules import crontab
from celery.task import task, periodic_task
from django.conf import settings
from geonode.contrib.services.models import WebServiceHarvestLayersJob, WebServiceRegistrationJob
from geonode.contrib.services.views import update_layers, register_service_by_type, _register_indexed_layers
from geonode.maps import autocomplete_light_registry


@task
def import_indexed_wms_service_layers(service, wms=None, owner=None):
    _register_indexed_layers(service, wms=wms, owner=owner)


@task
def import_indexed_service(url, type, username=None, password=None, owner=None):
    register_service_by_type(url, type, username=username, password=password, owner=owner)

@periodic_task(run_every=crontab(minute=settings.SERVICE_UPDATE_INTERVAL))
def harvest_service_layers():
    harvestJobs = WebServiceHarvestLayersJob.objects.all()
    for job in harvestJobs.exclude(status="process"):
        try:
            job.status = "process"
            job.save()
            update_layers(job.service)
            job.delete()
        except Exception, e:
            print e
            job.status = 'failed'
            job.save()

@periodic_task(run_every=crontab(minute=settings.SERVICE_UPDATE_INTERVAL))
def import_service():
    boundsJobs = WebServiceRegistrationJob.objects.all()
    for job in boundsJobs.exclude(status="process"):
        try:
            job.status = "process"
            job.save()
            register_service_by_type(job.base_url, job.type, username=None, password=None, owner=None)
            job.delete()
        except Exception, e:
            job.status = 'failed'
            job.save()
            print e