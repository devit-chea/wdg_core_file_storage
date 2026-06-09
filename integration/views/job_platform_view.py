import secrets
import requests
from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from rest_framework import status, permissions
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from apps.integration.models.job_platform import (
    JobPlatformHandshake,
    JobPlatformPartner,
)
from apps.integration.serializers.integration_serializer import TokenExchangeSerializer
from apps.integration.utils.crypto_utils import hash_sha256, base64url_encode_sha256


class TokenExchangeView(APIView):
    """
    Processes sequence handshake verification logic.
    """

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = TokenExchangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        # Extracted directly from browser session state
        code_verifier = request.headers.get("X-Code-Verifier", "")
        with transaction.atomic():
            try:
                handshake = JobPlatformHandshake.objects.select_for_update().get(
                    temporary_code=data["temporary_code"]
                )
            except JobPlatformHandshake.DoesNotExist:
                return Response(
                    {"status": "error", "message": "Handshake token not found."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if handshake.expires_at <= timezone.now():
                handshake.delete()
                return Response(
                    {"status": "error", "message": "Handshake expired."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if handshake.state != data["state"]:
                return Response(
                    {"status": "error", "message": "CSRF state mismatch."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            # Match PKCE Formula validation assertion
            if base64url_encode_sha256(code_verifier) != handshake.code_challenge:
                return Response(
                    {"status": "error", "message": "PKCE verification failed."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            # Generate dynamic runtime outbound Key_Beta string
            key_beta = f"job_outbound_{secrets.token_hex(32)}"
            key_beta_hash = hash_sha256(key_beta)

            exist_partner = JobPlatformPartner.objects.filter(
                organization_id=handshake.organization_id
            ).exists()
            if exist_partner:
                return Response(
                    {"status": "error", "message": "Organization already integrated."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            partner = JobPlatformPartner.objects.create(
                organization_id=handshake.organization_id,
                partner_tenant_id=data["erp_company_id"],
                partner_outbound_key=key_beta,
                partner_outbound_hash=key_beta_hash,  # Optimizes revocation lookups
                partner_inbound_key=data["erp_outbound_key"],
                status="active",
            )
            handshake.delete()
        return Response(
            {
                "status": "success",
                "message": "Integration linked successfully",
                "job_platform_org_id": partner.organization_id,
                "job_outbound_key": partner.partner_outbound_key,
            },
            status=status.HTTP_200_OK,
        )


class DropIntegrationView(APIView):
    """
    ENDPOINT 2: https://api.jobplatform.com/v1/integration/disconnect
    Called synchronously by the ERP backend to tear down integration lines.
    """

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header or not auth_header.startswith("Bearer "):
            return Response(
                {"status": "error", "message": "Unauthorized"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        incoming_key_beta = auth_header.split(" ")[1]
        incoming_hash = hash_sha256(incoming_key_beta)
        with transaction.atomic():
            try:
                # O(1) indexed lookup instead of slow database text looping
                partner = JobPlatformPartner.objects.select_for_update().get(
                    partner_outbound_hash=incoming_hash, status="active"
                )
                partner.delete()  # Cascades to user mapping tables
            except JobPlatformPartner.DoesNotExist:
                return Response(
                    {"status": "error", "message": "Forbidden: Token invalid."},
                    status=status.HTTP_403_FORBIDDEN,
                )
        return Response(
            {"status": "success", "message": "Connection terminated"},
            status=status.HTTP_200_OK,
        )


class InitializeHandshakeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        organization_id = str(request.user.company_id)

        if JobPlatformPartner.objects.filter(
            organization_id=organization_id,
            status="active",
        ).exists():
            return Response(
                {
                    "status": "error",
                    "message": "Organization already integrated.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        JobPlatformHandshake.objects.filter(organization_id=organization_id).delete()

        temporary_code = f"code_{secrets.token_hex(24)}"
        state = f"state_{secrets.token_hex(24)}"

        code_verifier = secrets.token_urlsafe(64)

        code_challenge = base64url_encode_sha256(code_verifier)

        JobPlatformHandshake.objects.create(
            temporary_code=temporary_code,
            state=state,
            code_challenge=code_challenge,
            organization_id=organization_id,
            expires_at=timezone.now() + timedelta(minutes=10),
        )

        return Response(
            {
                "status": "success",
                "state": state,
                "temporary_code": temporary_code,
                "code_challenge": code_challenge,
                "code_verifier": code_verifier,
            },
            status=status.HTTP_201_CREATED,
        )


class ErpUserLookupProxyView(APIView):
    """
    ConnectJob frontend calls this endpoint.

    This view calls Wing Digital server-to-server.
    Frontend never sees integration keys.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        organization_id = str(request.user.base_company.id)

        try:
            partner = JobPlatformPartner.objects.get(
                organization_id=organization_id,
                status="active",
            )
        except JobPlatformPartner.DoesNotExist:
            return Response(
                {
                    "status": "error",
                    "message": "Integration is not active.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # Key Alpha: ConnectJob -> Wing Digital
        key_alpha = partner.partner_inbound_key
        erp_company_id = partner.partner_tenant_id

        erp_api_url = "http://127.0.0.1:8000/api/connector-integration/users"

        try:
            erp_response = requests.get(
                url=erp_api_url,
                headers={
                    "X-CONNECTOR-KEY": f"{key_alpha}",
                },
                params={
                    "company_id": erp_company_id,
                    "paging": True,
                },
                # timeout=10,
            )
        except requests.RequestException as exc:
            return Response(
                {
                    "status": "error",
                    "message": "Wing Digital server could not be reached.",
                    "details": str(exc),
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

        if erp_response.status_code != 200:
            return Response(
                {
                    "status": "error",
                    "message": "Wing Digital rejected user lookup request.",
                    "details": erp_response.text,
                },
                status=erp_response.status_code,
            )

        return Response(
            erp_response.json(),
            status=status.HTTP_200_OK,
        )


class DropIntegrationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        connector_key = request.headers.get("X-CONNECTOR-KEY")

        if not connector_key:
            return Response(
                {
                    "status": "error",
                    "message": "Missing connector key.",
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        incoming_hash = hash_sha256(connector_key)

        partner = JobPlatformPartner.objects.filter(
            partner_outbound_hash=incoming_hash,
            status="active",
        ).first()

        if not partner:
            return Response(
                {
                    "status": "error",
                    "message": "Invalid connector key.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        partner.status = "disconnected"
        partner.save(update_fields=["status"])

        return Response(
            {
                "status": "success",
                "message": "ConnectJob integration disconnected.",
            },
            status=status.HTTP_200_OK,
        )
