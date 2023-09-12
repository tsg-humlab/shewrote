from django.contrib import admin
from .models import (Person, Collective, Work, Edition, Place, Membership, Authorship, Publication, RelatedPersonWork,
                     RelatedPersonEdition)

admin.site.register(Person)
admin.site.register(Collective)
admin.site.register(Work)
admin.site.register(Edition)
admin.site.register(Place)
admin.site.register(Membership)
admin.site.register(Authorship)
admin.site.register(Publication)
admin.site.register(RelatedPersonWork)
admin.site.register(RelatedPersonEdition)
