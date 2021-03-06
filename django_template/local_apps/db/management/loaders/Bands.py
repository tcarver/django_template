from db.models import Cvterm, Organism, Feature, Featureloc
from db.management.loaders.Utils import UtilsManager
from django.core.exceptions import ObjectDoesNotExist
import logging
import gzip
import re

# Get an instance of a logger
logger = logging.getLogger(__name__)


class BandsManager:

    def create_bands(self, **options):
        ''' Create cytological band features '''
        if options['org']:
            org = options['org']
        else:
            org = 'human'

        cv = self._gstain()
        organism = Organism.objects.get(common_name=org)
        f = gzip.open(options['bands'], 'rb')
        for line in f:
            parts = re.split('\t', line.decode("utf-8"))
            name = parts[0]+'_'+parts[3]
            try:
                cvterm = Cvterm.objects.get(cv=cv, name=parts[4].rstrip())
                feature = Feature(organism=organism, uniquename=name,
                                  name=parts[3], type=cvterm, is_analysis=0,
                                  is_obsolete=0)
                print('create feature... '+name+' on '+parts[0])
                srcfeature = (Feature.objects
                              .get(organism=organism,  # @UndefinedVariable
                                   uniquename=parts[0]))
                print('get srcfeature... '+parts[0])
                fmin = int(parts[1])-1
                feature.save()
                featureloc = Featureloc(feature=feature, srcfeature=srcfeature,
                                        fmin=fmin, fmax=parts[2], locgroup=0,
                                        rank=0)
                featureloc.save()
                print('loaded feature... '+name+' on '+srcfeature.uniquename)
            except ObjectDoesNotExist as e:
                logger.warn("WARNING:: NOT LOADED "+name)
                logger.warn(e)
        return

    def _gstain(self):
        '''
        Set up the G-staining ontology and return the CV object
        '''
        gstainList = []
        gstains = ['gpos100', 'gpos', 'gpos75', 'gpos66', 'gpos50',
                   'gpos33', 'gpos25', 'gvar', 'gneg', 'acen', 'stalk']
        for gstain in gstains:
            gstainList.append(Cvterm(name=gstain, definition=gstain))
        utils = UtilsManager()
        return utils.create_cvterms("gstain", "Giemsa banding", gstainList)
