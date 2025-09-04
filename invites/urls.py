from django.urls import path
from .views import (
    InviteListCreateView,
    InviteDetailView,
    InviteDetailByCodeView,
    UpdateInviteStatusView,
    VerifyInviteView,
    CaptureVisitorDataView,
)

urlpatterns = [
    # Admin usage (list + create)
    path("invites/", InviteListCreateView.as_view(), name="invite-list-create"),

    # Admin usage (detail by primary key)
    path("invites/<int:pk>/", InviteDetailView.as_view(), name="invite-detail"),

    # Admin + User usage (detail by UUID)
    path("invites/<uuid:invite_code>/", InviteDetailByCodeView.as_view(), name="invite-detail-code"),

    # Status update (admin/guards/etc.)
    path("invites/<int:pk>/status/", UpdateInviteStatusView.as_view(), name="invite-status"),

    # User flow (verify + capture)
    path("invites/verify/", VerifyInviteView.as_view(), name="invite-verify"),
    path("invites/capture/", CaptureVisitorDataView.as_view(), name="invite-capture"),
]
