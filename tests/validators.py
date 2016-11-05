from unittest import TestCase

from adapters import DeclarativeValidationNode, Schema, ValidationError


class ValidatorsTest(TestCase):
    def assertHasValidationError(self, result, message, field=None):
        self.assertFalse(result.is_valid)
        error = ValidationError(message, field)
        self.assertIn(error, result.errors)

    def _test_username_schema(self, schema):
        self.assertHasValidationError(
            schema.validate({}),
            'missing data: username'
        )
        self.assertHasValidationError(
            schema.validate({'username': 'foobar'}),
            'invalid username', 'username'
        )
        result = schema.validate({'username': 'admin'})
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

        schema = Schema(ValidateUsername)
        self._test_username_schema(schema)

    def test_staticmethod_validator(self):
        class ValidateUsername(DeclarativeValidationNode):
            inputs = {'username'}
            outputs = {'username'}

            @staticmethod
            def validate_username(data, **kwargs):
                if data['username'] != 'admin':
                    raise ValidationError('invalid username', 'username')

        schema = Schema(ValidateUsername)
        self._test_username_schema(schema)

    def test_coercing(self):
        class CoerceUsernameUppercase(DeclarativeValidationNode):
            inputs = {'username'}

            @staticmethod
            def coerce_username_uppercase(data, **kwargs):
                data['username'] = data['username'].upper()

        schema = Schema(CoerceUsernameUppercase)
        result = schema.validate({'username': 'foo'})
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
            depends = [ValidateEmail]

            @staticmethod
            def validate_email_domain(data, **kwargs):
                email = data['email']
                if email.partition('@')[2] != 'example.com':
                    raise ValidationError(
                        'e-mail address must be from example.com', 'email'
                    )

        schema = Schema(ValidateEmailDomain)
        self.assertHasValidationError(
            schema.validate({'email': 'qwe'}),
            'invalid e-mail address', 'email'
        )
        self.assertHasValidationError(
            schema.validate({'email': 'qwe@example.org'}),
            'e-mail address must be from example.com', 'email'
        )
        self.assertTrue(schema.validate({'email': 'qwe@example.com'}).is_valid)

    def test_context_data(self):
        class ValidateUsername(DeclarativeValidationNode):
            inputs = {'username'}

            @staticmethod
            def validate_username(data, user, **kwargs):
                if data['username'] != user:
                    raise ValidationError('unexpected username', 'username')

        schema = Schema(ValidateUsername)
        self.assertHasValidationError(
            schema.validate({'username': 'foo'}, user='bar'),
            'unexpected username', 'username'
        )
        self.assertTrue(schema.validate({'username': 'foo'}, user='foo').is_valid)
