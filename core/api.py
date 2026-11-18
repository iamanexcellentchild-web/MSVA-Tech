"""Read-only JSON API for tracks, plus the signed-in user's applications."""

from rest_framework import generics, permissions, serializers

from .models import Application, SyllabusWeek, Track


class SyllabusWeekSerializer(serializers.ModelSerializer):
    topics = serializers.ListField(source="topic_list", read_only=True)

    class Meta:
        model = SyllabusWeek
        fields = ["week_number", "title", "summary", "topics", "deliverable"]


class TrackListSerializer(serializers.ModelSerializer):
    url = serializers.CharField(source="get_absolute_url", read_only=True)

    class Meta:
        model = Track
        fields = ["title", "slug", "icon", "tagline", "short_description", "duration", "level", "url"]


class TrackDetailSerializer(TrackListSerializer):
    weeks = SyllabusWeekSerializer(many=True, read_only=True)
    outcomes = serializers.ListField(source="outcome_list", read_only=True)
    tools = serializers.ListField(source="tool_list", read_only=True)

    class Meta(TrackListSerializer.Meta):
        fields = TrackListSerializer.Meta.fields + [
            "overview", "mode", "certificate", "cover_image", "syllabus_image",
            "syllabus_image_caption", "outcomes", "tools", "weeks",
        ]


class ApplicationSerializer(serializers.ModelSerializer):
    track = TrackListSerializer(read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Application
        fields = ["track", "full_name", "status", "status_display", "created_at"]


class TrackListAPI(generics.ListAPIView):
    queryset = Track.objects.filter(is_published=True)
    serializer_class = TrackListSerializer
    permission_classes = [permissions.AllowAny]


class TrackDetailAPI(generics.RetrieveAPIView):
    queryset = Track.objects.filter(is_published=True).prefetch_related("weeks")
    serializer_class = TrackDetailSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "slug"


class MyApplicationsAPI(generics.ListAPIView):
    serializer_class = ApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Application.objects.filter(user=self.request.user).select_related("track")
