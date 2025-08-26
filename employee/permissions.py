# permissions.py
from rest_framework import permissions

class EmployeeRolePermission(permissions.BasePermission):
    """
    Custom permission for role-based access to Employee API.
    """

    def has_permission(self, request, view):
        # Allow authenticated users only
        if not request.user.is_authenticated:
            return False

        # Superadmin can do anything
        if request.user.role == "superadmin":
            return True

        # Admin can access list, retrieve, create, update, but not delete
        if request.user.role == "admin":
            if view.action == "destroy":
                return False
            return True

        # Employee can only retrieve their own info
        if request.user.role == "employee":
            if view.action in ["retrieve", "list"]:
                return True
            return False

        return False

    def has_object_permission(self, request, view, obj):
        # Superadmin can do anything
        if request.user.role == "superadmin":
            return True

        # Admin cannot delete, can update or view
        if request.user.role == "admin":
            if view.action == "destroy":
                return False
            return True

        # Employee can only view their own employee object
        if request.user.role == "employee":
            return obj.user == request.user

        return False
