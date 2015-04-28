from django.contrib.auth.models import User, Group

from candidates.models import (
    TRUSTED_TO_MERGE_GROUP_NAME, TRUSTED_TO_LOCK_GROUP_NAME
)
from official_documents.models import DOCUMENT_UPLOADERS_GROUP_NAME

class TestUserMixin(object):

    @classmethod
    def setUpClass(cls):
        cls.user = User.objects.create_user(
            'john',
            'john@example.com',
            'notagoodpassword',
        )
        cls.user_who_can_merge = User.objects.create_user(
            'alice',
            'alice@example.com',
            'alsonotagoodpassword',
        )
        cls.user_who_can_lock = User.objects.create_user(
            'charles',
            'charles@example.com',
            'alsonotagoodpassword',
        )
        cls.user_who_can_upload_documents = User.objects.create_user(
            'delilah',
            'delilah@example.com',
            'alsonotagoodpassword',
        )
        merger_group = Group.objects.get(name=TRUSTED_TO_MERGE_GROUP_NAME)
        merger_group.user_set.add(cls.user_who_can_merge)
        locker_group = Group.objects.get(name=TRUSTED_TO_LOCK_GROUP_NAME)
        locker_group.user_set.add(cls.user_who_can_lock)
        uploader_group = Group.objects.get(name=DOCUMENT_UPLOADERS_GROUP_NAME)
        uploader_group.user_set.add(cls.user_who_can_upload_documents)
        for u in cls.user, cls.user_who_can_merge, cls.user_who_can_lock, cls.user_who_can_upload_documents:
            terms = u.terms_agreement
            terms.assigned_to_dc = True
            terms.save()
        cls.user_refused = User.objects.create_user(
            'johnrefused',
            'johnrefused@example.com',
            'notagoodpasswordeither',
        )

    @classmethod
    def tearDownClass(cls):
        cls.user_refused.delete()
        cls.user_who_can_upload_documents.delete()
        cls.user_who_can_lock.delete()
        cls.user_who_can_merge.delete()
        cls.user.delete()
