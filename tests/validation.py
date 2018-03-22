from unittest import TestCase

from adapters import DeclarativeValidationNode, ValidationError, ValidationTree


class ValidatorsTest(TestCase):
    def assertHasValidationError(self, result, message, field=None):
        self.assertFalse(result.is_valid)
        error = ValidationError(message, field)
        self.assertIn(error, result.errors)

    def _test_username_tree(self, tree):
        self.assertHasValidationError(
            tree.validate({}),
            'missing data: username'
        )
        self.assertHasValidationError(
            tree.validate({'username': 'foobar'}),
            'invalid username', 'username'
        )
        result = tree.validate({'username': 'admin'})
        self.assertTrue(result.is_valid)
        self.assertEqual(result.data, {'username': 'admin'})

    def test_simple_validation(self):
        def validate_username(data, **kwargs):
            if data['username'] != 'admin':
                raise ValidationError('invalid username', 'username')

        class ValidateUsername(DeclarativeValidationNode):
            inputs = {'username'}
            outputs = {'username'}
            validators = [validate_username]

        tree = ValidationTree(ValidateUsername)
        self._test_username_tree(tree)

    def test_staticmethod_validator(self):
        class ValidateUsername(DeclarativeValidationNode):
            inputs = {'username'}
            outputs = {'username'}

            @staticmethod
            def validate_username(data, **kwargs):
                if data['username'] != 'admin':
                    raise ValidationError('invalid username', 'username')

        tree = ValidationTree(ValidateUsername)
        self._test_username_tree(tree)

    def test_coercing(self):
        class CoerceUsernameUppercase(DeclarativeValidationNode):
            inputs = {'username'}

            @staticmethod
            def coerce_username_uppercase(data, **kwargs):
                data['username'] = data['username'].upper()

        tree = ValidationTree(CoerceUsernameUppercase)
        result = tree.validate({'username': 'foo'})
        self.assertTrue(result.is_valid)
        self.assertEqual(result.data, {'username': 'FOO'})

    def test_dependencies(self):
        class ValidateEmail(DeclarativeValidationNode):
            inputs = {'email'}

            @staticmethod
            def validate_is_email(data, **kwargs):
                if '@' not in data['email']:
                    raise ValidationError('invalid e-mail address', 'email')

        class ValidateEmailDomain(DeclarativeValidationNode):
            dependencies = [ValidateEmail]

            @staticmethod
            def validate_email_domain(data, **kwargs):
                email = data['email']
                if email.partition('@')[2] != 'example.com':
                    raise ValidationError(
                        'e-mail address must be from example.com', 'email'
                    )

        tree = ValidationTree(ValidateEmailDomain)
        self.assertHasValidationError(
            tree.validate({'email': 'qwe'}),
            'invalid e-mail address', 'email'
        )
        self.assertHasValidationError(
            tree.validate({'email': 'qwe@example.org'}),
            'e-mail address must be from example.com', 'email'
        )
        self.assertTrue(tree.validate({'email': 'qwe@example.com'}).is_valid)

    def test_context_data(self):
        class ValidateUsername(DeclarativeValidationNode):
            inputs = {'username'}

            @staticmethod
            def validate_username(data, user, **kwargs):
                if data['username'] != user:
                    raise ValidationError('unexpected username', 'username')

        tree = ValidationTree(ValidateUsername)
        self.assertHasValidationError(
            tree.validate({'username': 'foo'}, user='bar'),
            'unexpected username', 'username'
        )
        self.assertTrue(tree.validate({'username': 'foo'}, user='foo').is_valid)

    def test_revalidate(self):
        log = set()

        class ValidateUsername(DeclarativeValidationNode):
            inputs = {'username'}

            @staticmethod
            def validate_username(data, **kwargs):
                if len(data['username']) > 10:
                    log.add('username fail')
                    raise ValidationError('username is too long', 'username')
                log.add('username')

        class ValidateEmail(DeclarativeValidationNode):
            inputs = {'email'}

            @staticmethod
            def validate_email(data, **kwargs):
                if '@' not in data['email']:
                    log.add('email fail')
                    raise ValidationError('invalid e-mail address', 'email')
                log.add('email')

        class ValidateUser(DeclarativeValidationNode):
            dependencies = {ValidateUsername, ValidateEmail}

            @staticmethod
            def validate_user(data, **kwargs):
                if data['username'] not in data['email']:
                    log.add('user fail')
                    raise ValidationError('e-mail must contain username', 'email')
                log.add('user')

        tree = ValidationTree(ValidateUser)
        result = tree.validate({'username': 'foouser', 'email': 'foo'})
        self.assertEqual(log, {'username', 'email fail'})

        log = set()
        tree.revalidate(result, {'email': 'bar'})
        self.assertEqual(log, {'email fail'})

        log = set()
        tree.revalidate(result, {'username': 'baruser', 'email': 'bar'})
        self.assertEqual(log, {'username', 'email fail'})

        log = set()
        tree.revalidate(result, {'username': 'q' * 20, 'email': 'bar@qqq'})
        self.assertEqual(log, {'username fail', 'email'})

        log = set()
        tree.revalidate(result, {'email': 'foo@qqq'})
        self.assertEqual(log, {'email', 'user fail'})

        log = set()
        tree.revalidate(result, {'email': 'foouser@qqq'})
        self.assertEqual(log, {'email', 'user'})
