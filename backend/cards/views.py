from rest_framework.response import Response
from rest_framework.views import APIView

from . import services
from .serializers import ChangePinSerializer


class ChangePinView(APIView):
    def post(self, request):
        serializer = ChangePinSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data
        card = services.change_first_time_pin(
            card_number=d["card_number"],
            first_time_pin=d["first_time_pin"],
            id_document_number=d["id_document_number"],
            new_pin=d["new_pin"],
        )
        return Response({"message": "Your PIN has been changed.", "masked_number": card.masked_number})
