from celery.schedules import crontab
from celery.task import task, periodic_task
from django.conf import settings
from geonode.contrib.services.models import WebServiceHarvestLayersJob, WebServiceRegistrationJob
from geonode.contrib.services.views import update_layers, register_service_by_type, _register_indexed_layers
from geonode.maps import autocomplete_light_registry

@periodic_task(run_every=crontab(minute=settings.SERVICE_UPDATE_INTERVAL))
def harvest_service_layers():
    if WebServiceHarvestLayersJob.objects.filter(status="process").count() == 0:
        for job in WebServiceHarvestLayersJob.objects.exclude(status="process").exclude(status="done"):
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