import uuid
import os
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.shortcuts import get_object_or_404
from geonode.upload import upload
from geonode.geoserver.uploader import uploader
from geonode.upload.views import _ASYNC_UPLOAD, save_step_view as geonode_save_step_view, \
    time_step_view, srs_step_view, final_step_view, csv_step_view, _SESSION_KEY, \
    rename_and_prepare, find_sld,  get_upload_type,  \
    get_previous_step, _next_step_response, _error_response
from geonode.upload.models import Upload
from geonode.upload.forms import LayerUploadForm
from geonode.worldmap.layerutils.forms import WorldMapLayerUploadForm
from django.utils.html import escape



CHARSETS = [
    ['', 'None/Unknown'],
    ['UTF-8', 'UTF-8/Unicode'],
    ['ISO-8859-1', 'Latin1/ISO-8859-1'],
    ['ISO-8859-2', 'Latin2/ISO-8859-2'],
    ['ISO-8859-3', 'Latin3/ISO-8859-3'],
    ['ISO-8859-4', 'Latin4/ISO-8859-4'],
    ['ISO-8859-5', 'Latin5/ISO-8859-5'],
    ['ISO-8859-6', 'Latin6/ISO-8859-6'],
    ['ISO-8859-7', 'Latin7/ISO-8859-7'],
    ['ISO-8859-8', 'Latin8/ISO-8859-8'],
    ['ISO-8859-9', 'Latin9/ISO-8859-9'],
    ['ISO-8859-10','Latin10/ISO-8859-10'],
    ['ISO-8859-13','Latin13/ISO-8859-13'],
    ['ISO-8859-14','Latin14/ISO-8859-14'],
    ['ISO8859-15','Latin15/ISO-8859-15'],
    ['Big5', 'BIG5'],
    ['EUC-JP','EUC-JP'],
    ['EUC-KR','EUC-KR'],
    ['GBK','GBK'],
    ['GB18030','GB18030'],
    ['Shift_JIS','Shift_JIS'],
    ['KOI8-R','KOI8-R'],
    ['KOI8-U','KOI8-U'],
    ['windows-874', 'Windows CP874'],
    ['windows-1250', 'Windows CP1250'],
    ['windows-1251', 'Windows CP1251'],
    ['windows-1252', 'Windows CP1252'],
    ['windows-1253', 'Windows CP1253'],
    ['windows-1254', 'Windows CP1254'],
    ['windows-1255', 'Windows CP1255'],
    ['windows-1256', 'Windows CP1256'],
    ['windows-1257', 'Windows CP1257'],
    ['windows-1258', 'Windows CP1258']
]



def save_step_view(req, session):
    if req.method == 'GET':
        if 'tab' in req.path:
            return render_to_response('upload/layer_upload_tab.html',
            RequestContext(req, {
            'async_upload' : _ASYNC_UPLOAD,
            'incomplete' : Upload.objects.get_incomplete_uploads(req.user),
            'charsets': CHARSETS
        }))
        else:
            return render_to_response('upload/layer_upload.html',
            RequestContext(req, {
            'async_upload' : _ASYNC_UPLOAD,
            'incomplete' : Upload.objects.get_incomplete_uploads(req.user),
            'charsets': CHARSETS
        }))

    assert session is None

    form = WorldMapLayerUploadForm(req.POST, req.FILES)
    tempdir = None

    if form.is_valid():
        tempdir, base_file = form.write_files()
        base_file = rename_and_prepare(base_file)
        name, ext = os.path.splitext(os.path.basename(base_file))
        import_session = upload.save_step(req.user, name, base_file, overwrite=False)
        sld = find_sld(base_file)
        upload_type = get_upload_type(base_file)
        upload_session = req.session[_SESSION_KEY] = upload.UploaderSession(
            tempdir=tempdir,
            base_file=base_file,
            name=name,
            import_session=import_session,
            layer_abstract=form.cleaned_data["abstract"],
            layer_title=form.cleaned_data["layer_title"],
            permissions=form.cleaned_data["permissions"],
            keywords=form.cleaned_data["keywords"],
            import_sld_file = sld,
            upload_type = upload_type,
            geogit=form.cleaned_data['geogit'],
            geogit_store=form.cleaned_data['geogit_store'],
            time=form.cleaned_data['time']
        )
        return _next_step_response(req, upload_session, force_ajax=True)
    else:
        errors = []
        for e in form.errors.values():
            errors.extend([escape(v) for v in e])
        return _error_response(req, errors=errors)





_steps = {
    'save': save_step_view,
    'time': time_step_view,
    'srs' : srs_step_view,
    'final': final_step_view,
    'csv': csv_step_view,
}


@login_required
def view(req, step):
    """Main uploader view - overrides geonode.upload.views.view - check there for updates """

    upload_session = None

    if step is None:
        if 'id' in req.GET:
            # upload recovery
            upload_obj = get_object_or_404(Upload, import_id=req.GET['id'], user=req.user)
            session = upload_obj.get_session()
            if session:
                req.session[_SESSION_KEY] = session
                return _next_step_response(req, session)

        step = 'save'

        # delete existing session
        if _SESSION_KEY in req.session:
            del req.session[_SESSION_KEY]

    else:
        if not _SESSION_KEY in req.session:
            return render_to_response("upload/layer_upload_invalid.html", RequestContext(req,{}))
        upload_session = req.session[_SESSION_KEY]

    try:
        if req.method == 'GET' and upload_session:
            # set the current step to match the requested page - this
            # could happen if the form is ajax w/ progress monitoring as
            # the advance would have already happened @hacky
            upload_session.completed_step = get_previous_step(upload_session, step)

        if step == "undefined":
            step = "final"
        resp = _steps[step](req, upload_session)
        # must be put back to update object in session
        if upload_session:
            req.session[_SESSION_KEY] = upload_session
        elif _SESSION_KEY in req.session:
            upload_session = req.session[_SESSION_KEY]
        if upload_session:
            Upload.objects.update_from_session(upload_session)
        return resp
    except upload.UploadException, e:
        return _error_response(req, errors=e.args)
    except uploader.BadRequest, e:
        return _error_response(req, errors=e.args)
    except Exception, e:
        if upload_session:
            # @todo probably don't want to do this
            upload_session.cleanup()
        code = uuid.uuid4()
        errors= ['Unexpected Error:','Please report the following code: %s' % e.message]
        return _error_response(req, exception=e, errors=errors)
