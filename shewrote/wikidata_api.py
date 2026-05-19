import requests
from django.conf import settings


def get_wikidata_data(url):
    response = requests.get(url, headers={'accept': 'application/json',
                                          'Authorization': f'Bearer {settings.WIKIDATA_API_KEY}'})
    return response.json() if response.status_code == requests.codes.ok else None


def get_wikidata_statements(id):
    return get_wikidata_data(settings.WIKIDATA_STATEMENTS_URL.format(id))


def get_wikidata_label(id, language='en'):
    return get_wikidata_data(settings.WIKIDATA_LABEL_URL.format(id, language))
