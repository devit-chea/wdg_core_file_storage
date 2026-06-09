from rest_framework import serializers

class TokenExchangeSerializer(serializers.Serializer):
    temporary_code = serializers.CharField(max_length=64)
    state = serializers.CharField(max_length=64)
    erp_company_id = serializers.CharField(max_length=100)
    erp_outbound_key = serializers.CharField(max_length=500)  # Key_Alpha
    code_challenge = serializers.CharField(max_length=64)