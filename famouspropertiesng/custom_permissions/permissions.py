from rest_framework.views import exception_handler
from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework import permissions

class PublicReadOnly(BasePermission):
    """
    Allows read-only access to anyone,
    but write/edit/delete access only to authenticated users.
    """
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission: Only the owner of an object can edit or delete it.
    Others can only read (GET, HEAD, OPTIONS).
    """

    message = "Only the owner of this product can modify it."

    def has_object_permission(self, request, view, obj):
        # SAFE_METHODS = ('GET', 'HEAD', 'OPTIONS')  → read-only actions
        if request.method in permissions.SAFE_METHODS:
            return True

        # For write actions (PUT, PATCH, DELETE), check ownership
        return obj.user == request.user


def custom_exception_handler(exc, context):
    # Call DRF's default handler first
    response = exception_handler(exc, context)

    # If we got a response, modify it
    if response is not None and "detail" in response.data:
        # Rename 'detail' → 'error'
        response.data = {
            "error": response.data["detail"]
        }

    return response