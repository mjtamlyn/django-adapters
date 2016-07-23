from unittest import TestCase

from adapters.validators import (
    EMail, Length, Schema, Type, UnicodeNormalize, ValidationError,
)


class ValidatorsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        class UsernameSchema(Schema):
            inputs = {'username'}
            outputs = {'username', 'username_normalized'}
            validators = [
                Type('username', str),
                Length('username', min=4, max=100),
                UnicodeNormalize('username', out='username_normalized'),
            ]

        class EMailSchema(Schema):
            inputs = {'email'}
            validators = [
                EMail('email'),
            ]

        class RegistrationSchema(Schema):
            depends = [UsernameSchema, EMailSchema]

            @staticmethod
            def validate_username_in_email(data, **kwargs):
                if data['username_normalized'] not in data['email']:
                    raise ValidationError("E-mail must contain username", field='email')

        cls.UsernameSchema = UsernameSchema
        cls.EMailSchema = EMailSchema
        cls.RegistrationSchema = RegistrationSchema

    def test_simple_validation(self):
        schema = self.UsernameSchema()
        validator = schema.validate({'username': 'foobar'})
        self.assertTrue(validator.is_valid)
        validator = schema.validate({'username': 'x'})
        self.assertFalse(validator.is_valid)

    def test_missing_field(self):
        schema = self.EMailSchema()
        validator = schema.validate({})
        self.assertFalse(validator.is_valid)

    def test_partial_validation(self):
        schema = self.RegistrationSchema()
        validator = schema.validate({'username': 'foobar', 'email': 'not an email address'})
        self.assertFalse(validator.is_valid)
        self.assertTrue(validator['username'].is_valid)
        self.assertFalse(validator['email'].is_valid)
        self.assertIn(ValidationError("invalid e-mail address"), validator['email'].errors)

        validator = schema.validate({'username': 'x', 'email': 'x@example.com'})
        self.assertFalse(validator.is_valid)
        self.assertFalse(validator['username'].is_valid)
        self.assertIn(
            ValidationError("field must have between 4 and 100 characters"),
            validator['username'].errors
        )
        self.assertTrue(validator['email'].is_valid)
        self.assertNotIn(ValidationError("E-mail must contain username"), validator.errors)

    def test_dependencies(self):
        schema = self.RegistrationSchema()
        self.assertEqual(schema.inputs, {'username', 'email'})
        self.assertEqual(schema.outputs, {'username', 'username_normalized', 'email'})

        validator = schema.validate({'username': 'foobar', 'email': 'barfoo@example.com'})
        self.assertFalse(validator.is_valid)
        self.assertIn(ValidationError("E-mail must contain username"), validator['email'].errors)

    def test_context_data(self):
        class LoggedInUserSchema(self.UsernameSchema):
            @staticmethod
            def validate_username_is_not_user(data, user, **kwargs):
                if data['username_normalized'] == user.username:
                    raise ValidationError("Already logged in with user", field='username')

        class User(object):
            def __init__(self, username):
                self.username = username

        schema = LoggedInUserSchema()
        validator = schema.validate({'username': 'foobar'}, User('barfoo'))
        self.assertFalse(validator.is_valid)
        self.assertIn(ValidationError("Already logged in with user"), validator['username'].errors)

    def test_adapter_compatibility(self):
        adapter = Adapter()  # XXX: mystery internal representation
        # here the schema could update the adapter with its inputs and outputs
        schema = self.RegistrationSchema(adapter)
        # here the schema object just takes the data out of the adapter and
        # maybe adds some "cleaned" values
        schema.validate(adapter)
