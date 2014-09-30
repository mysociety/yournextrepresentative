from django.contrib.auth.models import User

class TestUserMixin(object):

    @classmethod
    def setUpClass(cls):
        cls.user = User.objects.create_user(
            'john',
            'john@example.com',
            'notagoodpassword',
        )

    @classmethod
    def tearDownClass(cls):
        cls.user.delete()
