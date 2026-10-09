from rest_framework import serializers

from core import validators


class IssuedCardSerializer(serializers.Serializer):
    """Shown once, right after approval. Delivery of physical card/PIN is out of scope."""

    card_number = serializers.CharField()
    masked_number = serializers.CharField()
    card_type = serializers.CharField()
    credit_limit = serializers.DecimalField(max_digits=10, decimal_places=2)
    expires_on = serializers.DateField()
    first_time_pin = serializers.SerializerMethodField()

    def get_first_time_pin(self, obj):
        return self.context.get("first_time_pin")


class ChangePinSerializer(serializers.Serializer):
    card_number = serializers.CharField(max_length=19)
    first_time_pin = serializers.CharField(max_length=4)
    id_document_number = serializers.CharField(max_length=24)
    new_pin = serializers.CharField(max_length=4)
    confirm_pin = serializers.CharField(max_length=4)

    def validate_card_number(self, value):
        digits = value.replace(" ", "").replace("-", "")
        if len(digits) != 16 or not validators.passes_luhn(digits):
            raise serializers.ValidationError("Enter a valid 16-digit card number.")
        return digits

    def validate_first_time_pin(self, value):
        if not (value.isdigit() and len(value) == 4):
            raise serializers.ValidationError("The first-time PIN is 4 digits.")
        return value

    def validate_id_document_number(self, value):
        normalized = validators.normalize_document_number(value)
        if not normalized:
            raise serializers.ValidationError("Enter the ID document number from your application.")
        return normalized

    def validate_new_pin(self, value):
        problem = validators.pin_problem(value)
        if problem:
            raise serializers.ValidationError(problem)
        return value

    def validate(self, attrs):
        if attrs["new_pin"] != attrs["confirm_pin"]:
            raise serializers.ValidationError({"confirm_pin": "The two PINs do not match."})
        if attrs["new_pin"] == attrs["first_time_pin"]:
            raise serializers.ValidationError({"new_pin": "Choose a PIN different from the first-time PIN."})
        return attrs
