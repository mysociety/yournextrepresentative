from random import randint
import sys

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[-1].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def create_version_id():
    """Generate a random ID to use to identify a person version"""
    return "{0:016x}".format(randint(0, sys.maxint))
