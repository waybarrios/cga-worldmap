from modeltranslation.translator import translator, TranslationOptions
from geonode.maps.models import LayerCategory

class LayerCategoryTranslationOptions(TranslationOptions):
    fields = ('title', 'description',)

translator.register(LayerCategory, LayerCategoryTranslationOptions)