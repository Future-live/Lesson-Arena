from rest_framework import serializers


class SimpleMessageSerializer(serializers.Serializer):
    detail = serializers.CharField()
