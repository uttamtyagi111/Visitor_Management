from django.urls import path
from .views import (
    InviteListCreateView, InviteDetailView, ApproveInviteView,
    CheckInView, CheckOutView
)

urlpatterns = [
    path("invites/", InviteListCreateView.as_view(), name="invite-list-create"),
    path("invites/<int:pk>/", InviteDetailView.as_view(), name="invite-detail"),
    path("invites/<int:pk>/approve/", ApproveInviteView.as_view(), name="invite-approve"),
    path("invites/<int:pk>/checkin/", CheckInView.as_view(), name="invite-checkin"),
    path("invites/<int:pk>/checkout/", CheckOutView.as_view(), name="invite-checkout"),
]
