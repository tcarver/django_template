from django.shortcuts import render
from elastic.elastic_model import Elastic, ElasticQuery
from db.models import Featureloc
import re


def marker_page(request, marker):
    ''' Render a marker page '''
    query = ElasticQuery.query_match("id", marker)
    elastic = Elastic(query)
    context = elastic.get_result()
    _add_info(context)

    # get gene(s) overlapping position
    position = context['data'][0]['start']
    chrom = 'chr'+str(context['data'][0]['seqid'])
    featurelocs = (Featureloc.objects
                   .filter(fmin__lt=position)  # @UndefinedVariable
                   .filter(fmax__gt=position)  # @UndefinedVariable
                   .filter(srcfeature__uniquename=chrom)  # @UndefinedVariable
                   .filter(feature__type__name='gene'))  # @UndefinedVariable

    genes = []
    for loc in featurelocs:
        genes.append(loc.feature)
    context['genes'] = genes
    # page title
    if len(context["data"]) == 1 and "id" in context["data"][0]:
        context['title'] = "Marker - " + context["data"][0]["id"]

    return render(request, 'marker/marker.html', context,
                  content_type='text/html')


def _add_info(context):
    ''' Parse VCF INFO field and add to the elastic hit '''
    if 'info' not in context['data'][0]:
        return

    ''' Split and add INFO tags and values '''
    infos = re.split(';', context['data'][0]['info'])
    for info in infos:
        if "=" in info:
            parts = re.split('=', info)
            if parts[0] not in context['data'][0]:
                context['data'][0][parts[0]] = parts[1]
        else:
            if info not in context['data'][0]:
                context['data'][0][info] = ""
