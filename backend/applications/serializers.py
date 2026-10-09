from datetime import date

from rest_framework import serializers

from core import validators

from .models import CreditApplication, EmploymentType, IdDocumentType


class ApplicationInputSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=60)
    last_name = serializers.CharField(max_length=60)
    date_of_birth = serializers.DateField()
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=20)

    employment_type = serializers.ChoiceField(choices=EmploymentType.choices)
    employer_name = serializers.CharField(max_length=120)
    job_title = serializers.CharField(max_length=120)
    annual_salary = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0)
    existing_credit_cards = serializers.IntegerField(min_value=0, max_value=50, default=0)

    id_document_type = serializers.ChoiceField(choices=IdDocumentType.choices)
    id_document_number = serializers.CharField(max_length=24)

    def validate_first_name(self, v):
        return self._name(v)

    def validate_last_name(self, v):
        return self._name(v)

    @staticmethod
    def _name(value):
        value = value.strip()
        if not all(ch.isalpha() or ch in " '-." for ch in value):
            raise serializers.ValidationError("Use letters only (spaces, hyphens and apostrophes are fine).")
        return value

    def validate_date_of_birth(self, value):
        age = validators.age_in_years(value, date.today())
        if age < 18:
            raise serializers.ValidationError("Applicants must be at least 18 years old.")
        if age > 100:
            raise serializers.ValidationError("Enter a valid date of birth.")
        return value

    def validate_phone(self, value):
        if not validators.is_valid_phone(value):
            raise serializers.ValidationError("Enter 10–15 digits, with an optional leading +.")
        return validators.normalize_phone(value)

    def validate_annual_salary(self, value):
        if value <= 0:
            raise serializers.ValidationError("Annual salary must be greater than zero.")
        return value

    def validate(self, attrs):
        error = validators.check_document_number(attrs["id_document_type"], attrs["id_document_number"])
        if error:
            raise serializers.ValidationError({"id_document_number": error})
        attrs["id_document_number"] = validators.normalize_document_number(attrs["id_document_number"])
        return attrs


class ApplicationSerializer(serializers.ModelSerializer):
    applicant_name = serializers.SerializerMethodField()

    class Meta:
        model = CreditApplication
        fields = [
            "id", "status", "applicant_name", "credit_score", "card_type",
            "credit_limit", "decision_reason", "created_at", "decided_at",
        ]

    def get_applicant_name(self, obj):
        return f"{obj.customer.first_name} {obj.customer.last_name}"
