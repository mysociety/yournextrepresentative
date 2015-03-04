from django.contrib.auth.models import User

class TestUserMixin(object):

    @classmethod
    def setUpClass(cls):
        cls.user = User.objects.create_user(
            'john',
            'john@example.com',
            'notagoodpassword',
        )
        terms = cls.user.terms_agreement
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
        cls.user.delete()
