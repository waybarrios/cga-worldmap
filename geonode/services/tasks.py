from celery.schedules import crontab
from celery.task import task, periodic_task
from django.conf import settings
from geonode.services.models import WebServiceHarvestLayersJob, WebServiceRegistrationJob
from geonode.services.views import update_layers, register_service_by_type, _register_indexed_layers, _process_wms_service, _register_arcgis_url, _register_harvested_service, _register_ogp_service
from geonode.maps import autocomplete_light_registry
from django.core.mail import send_mail

@periodic_task(run_every=crontab(minute=settings.SERVICE_UPDATE_INTERVAL))
def harvest_service_layers():
    if WebServiceHarvestLayersJob.objects.filter(status="process").count() == 0:
        for job in WebServiceHarvestLayersJob.objects.filter(status="pending"):
            try:
                job.status = "process"
                job.save()
                update_layers(job.service)
                job.delete()
            except Exception, e:
                print e
                job.status = 'failed'
                job.save()
                send_mail('Service harvest failed', 'Service %d failed, error is %s' % (job.service.id, str(e)),
                    settings.DEFAULT_FROM_EMAIL, [email for admin,email in settings.ADMINS], fail_silently=True)

@periodic_task(run_every=crontab(minute=settings.SERVICE_UPDATE_INTERVAL))
def import_service():
    boundsJobs = WebServiceRegistrationJob.objects.all()
    for job in boundsJobs.filter(status="pending"):
        try:
            job.status = "process"
            job.save()

            if job.type in ["WMS","OWS"]:
                _process_wms_service(job.base_url,job.type, None, None)
            elif job.type == "REST":
                _register_arcgis_url(job.base_url, None, None)
            elif job.type == "CSW":
                _register_harvested_service(job.base_url, None, None)
            elif job.type == "OGP":
                _register_ogp_service(job.base_url)
            else:
                raise Exception("Type %s not implemented" % job.type)

            job.delete()
        except Exception, e:
            job.status = 'failed'
            job.save()
            print(str(e))
            send_mail('Service import failed', 'Service %s failed, error is %s' % (job.base_url, str(e)),
                      settings.DEFAULT_FROM_EMAIL, [email for admin,email in settings.ADMINS], fail_silently=True)
            raise e