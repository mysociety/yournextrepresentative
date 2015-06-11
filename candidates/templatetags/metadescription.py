from django import template
from django.conf import settings
from django.contrib.staticfiles.templatetags.staticfiles import static

register = template.Library()

@register.simple_tag
def metadescription(person, last_cons, today):
    output = person.name
    if person.last_party:
        last_party_name = person.last_party['name']
        if last_cons:
            election = last_cons[0]
            if is_post_election(election, today):
                output += " stood "
            else:
                output += " is standing "

        if last_party_name.strip() == "Independent":
            output += "as an independent candidate"
        else:
            party_words = last_party_name.strip().split()
            if party_words[0] != "The":
                output += "for the"
            else:
                output += "for"
            output += " %s" % last_party_name
        if last_cons:
            output += " in %s in %s" % (last_cons[1]['name'], last_cons[0])
    output += " - find out more on YourNextMP"
    return output

def is_post_election(election, today):
    return today > settings.ELECTIONS[election]['election_date']

@register.filter
def static_image_path(image_name, request):
    abs_path = static(image_name)
    return request.build_absolute_uri(abs_path)
