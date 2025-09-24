from django.urls import path
from .views import (
    InviteListCreateView,
    InviteDetailView,
    InviteDetailByCodeView,
    ReinviteAPIView,
    UpdateInviteStatusView,
    VerifyInviteView,
    CaptureinviteDataView,
    InviteTimelineAPIView,
    # ServePassView,
)

urlpatterns = [
    # Admin usage (list + create)
    path("invites/", InviteListCreateView.as_view(), name="invite-list-create"),
    
    # Reinvite endpoint
    path("invites/<int:pk>/reinvite/", ReinviteAPIView.as_view(), name="invite-reinvite"),


    # Admin usage (detail by primary key)
    path("invites/<int:pk>/", InviteDetailView.as_view(), name="invite-detail"),

    # Admin + User usage (detail by UUID)
    path("invites/<uuid:invite_code>/", InviteDetailByCodeView.as_view(), name="invite-detail-code"),

    # Status update (admin/guards/etc.)
    path("invites/<int:pk>/status/", UpdateInviteStatusView.as_view(), name="invite-status"),

    # User flow (verify + capture)
    path("invites/verify/", VerifyInviteView.as_view(), name="invite-verify"),
    path("invites/capture/", CaptureinviteDataView.as_view(), name="invite-capture"),
    
    # New: QR verification to serve the pass image
    # path("invites/verify-pass/<str:invite_code>/", ServePassView.as_view(), name="serve-pass"),
    
    path("invites/<int:pk>/timeline/", InviteTimelineAPIView.as_view(), name="invite-timeline"),

]
