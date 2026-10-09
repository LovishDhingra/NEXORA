from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from cards.serializers import IssuedCardSerializer

from . import services
from .models import CreditApplication
from .serializers import ApplicationInputSerializer, ApplicationSerializer


class ApplicationListCreate(APIView):
    def post(self, request):
        serializer = ApplicationInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        application, card, pin = services.submit_application(serializer.validated_data)

        body = ApplicationSerializer(application).data
        body["card"] = IssuedCardSerializer(card, context={"first_time_pin": pin}).data if card else None
        return Response(body, status=status.HTTP_201_CREATED)


class ApplicationDetail(APIView):
    def get(self, request, pk):
        application = get_object_or_404(CreditApplication.objects.select_related("customer"), pk=pk)
        body = ApplicationSerializer(application).data
        card = getattr(application, "card", None)
        body["card"] = (
            {"masked_number": card.masked_number, "card_type": card.card_type, "credit_limit": card.credit_limit}
            if card else None
        )
        return Response(body)
