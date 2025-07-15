"""This file and its contents are licensed under the Apache License 2.0. Please see the included NOTICE for copyright information and LICENSE for a copy of the license.
"""
import logging

import drf_yasg.openapi as openapi
from core.permissions import ViewClassPermission, all_permissions
from django.utils.decorators import method_decorator
from drf_yasg.utils import no_body, swagger_auto_schema
from rest_framework import generics, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from users.functions import check_avatar
from users.models import User
from users.serializers import HotkeysSerializer, UserSerializer, UserSerializerUpdate

logger = logging.getLogger(__name__)

_user_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='User ID'),
        'first_name': openapi.Schema(type=openapi.TYPE_STRING, description='First name of the user'),
        'last_name': openapi.Schema(type=openapi.TYPE_STRING, description='Last name of the user'),
        'username': openapi.Schema(type=openapi.TYPE_STRING, description='Username of the user'),
        'email': openapi.Schema(type=openapi.TYPE_STRING, description='Email of the user'),
        'avatar': openapi.Schema(type=openapi.TYPE_STRING, description='Avatar URL of the user'),
        'initials': openapi.Schema(type=openapi.TYPE_STRING, description='Initials of the user'),
        'phone': openapi.Schema(type=openapi.TYPE_STRING, description='Phone number of the user'),
        'allow_newsletters': openapi.Schema(
            type=openapi.TYPE_BOOLEAN, description='Whether the user allows newsletters'
        ),
    },
)


@method_decorator(
    name='update',
    decorator=swagger_auto_schema(
        tags=['Users'],
        x_fern_audiences=['internal'],
        operation_summary='Save user details',
        operation_description="""
    Save details for a specific user, such as their name or contact information, in Label Studio.
    """,
        manual_parameters=[
            openapi.Parameter(name='id', type=openapi.TYPE_INTEGER, in_=openapi.IN_PATH, description='User ID'),
        ],
        request_body=UserSerializer,
    ),
)
@method_decorator(
    name='list',
    decorator=swagger_auto_schema(
        tags=['Users'],
        x_fern_sdk_group_name='users',
        x_fern_sdk_method_name='list',
        x_fern_audiences=['public'],
        operation_summary='List users',
        operation_description='List the users that exist on the Label Studio server.',
    ),
)
@method_decorator(
    name='create',
    decorator=swagger_auto_schema(
        tags=['Users'],
        x_fern_sdk_group_name='users',
        x_fern_sdk_method_name='create',
        x_fern_audiences=['public'],
        operation_summary='Create new user',
        operation_description='Create a user in Label Studio.',
        request_body=_user_schema,
        responses={201: UserSerializer},
    ),
)
@method_decorator(
    name='retrieve',
    decorator=swagger_auto_schema(
        tags=['Users'],
        x_fern_sdk_group_name='users',
        x_fern_sdk_method_name='get',
        x_fern_audiences=['public'],
        operation_summary='Get user info',
        operation_description='Get info about a specific Label Studio user, based on the user ID.',
        manual_parameters=[
            openapi.Parameter(name='id', type=openapi.TYPE_INTEGER, in_=openapi.IN_PATH, description='User ID'),
        ],
        request_body=no_body,
        responses={200: UserSerializer},
    ),
)
@method_decorator(
    name='partial_update',
    decorator=swagger_auto_schema(
        tags=['Users'],
        x_fern_sdk_group_name='users',
        x_fern_sdk_method_name='update',
        x_fern_audiences=['public'],
        operation_summary='Update user details',
        operation_description="""
        Update details for a specific user, such as their name or contact information, in Label Studio.
        """,
        manual_parameters=[
            openapi.Parameter(name='id', type=openapi.TYPE_INTEGER, in_=openapi.IN_PATH, description='User ID'),
        ],
        request_body=_user_schema,
        responses={200: UserSerializer},
    ),
)
@method_decorator(
    name='destroy',
    decorator=swagger_auto_schema(
        tags=['Users'],
        x_fern_sdk_group_name='users',
        x_fern_sdk_method_name='delete',
        x_fern_audiences=['public'],
        operation_summary='Delete user',
        operation_description='Delete a specific Label Studio user.',
        manual_parameters=[
            openapi.Parameter(name='id', type=openapi.TYPE_INTEGER, in_=openapi.IN_PATH, description='User ID'),
        ],
        request_body=no_body,
    ),
)
class UserAPI(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_required = ViewClassPermission(
        GET=all_permissions.organizations_change,
        PUT=all_permissions.organizations_change,
        POST=all_permissions.organizations_change,
        PATCH=all_permissions.organizations_view,
        DELETE=all_permissions.organizations_change,
    )
    http_method_names = ['get', 'post', 'head', 'patch', 'delete']

    def get_queryset(self):
        return User.objects.filter(organizations=self.request.user.active_organization)

    @swagger_auto_schema(auto_schema=None, methods=['delete', 'post'])
    @action(detail=True, methods=['delete', 'post'], permission_required=all_permissions.avatar_any)
    def avatar(self, request, pk):
        if request.method == 'POST':
            avatar = check_avatar(request.FILES)
            request.user.avatar = avatar
            request.user.save()
            return Response({'detail': 'avatar saved'}, status=200)

        elif request.method == 'DELETE':
            request.user.avatar = None
            request.user.save()
            return Response(status=204)

    def get_serializer_class(self):
        if self.request.method in {'PUT', 'PATCH'}:
            return UserSerializerUpdate
        return super().get_serializer_class()

    def get_serializer_context(self):
        context = super(UserAPI, self).get_serializer_context()
        context['user'] = self.request.user
        return context

    def update(self, request, *args, **kwargs):
        return super(UserAPI, self).update(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        return super(UserAPI, self).list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        return super(UserAPI, self).create(request, *args, **kwargs)

    def perform_create(self, serializer):
        instance = serializer.save()
        self.request.user.active_organization.add_user(instance)

    def retrieve(self, request, *args, **kwargs):
        return super(UserAPI, self).retrieve(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        result = super(UserAPI, self).partial_update(request, *args, **kwargs)

        # throw MethodNotAllowed if read-only fields are attempted to be updated
        read_only_fields = self.get_serializer_class().Meta.read_only_fields
        for field in read_only_fields:
            if field in request.data:
                raise MethodNotAllowed('PATCH', detail=f'Cannot update read-only field: {field}')

        # newsletters
        if 'allow_newsletters' in request.data:
            user = User.objects.get(id=request.user.id)  # we need an updated user
            request.user.advanced_json = {  # request.user instance will be unchanged in request all the time
                'email': user.email,
                'allow_newsletters': user.allow_newsletters,
                'update-notifications': 1,
                'new-user': 0,
            }
        return result

    def destroy(self, request, *args, **kwargs):
        return super(UserAPI, self).destroy(request, *args, **kwargs)


@method_decorator(
    name='post',
    decorator=swagger_auto_schema(
        tags=['Users'],
        x_fern_sdk_group_name='users',
        x_fern_sdk_method_name='reset_token',
        x_fern_audiences=['public'],
        operation_summary='Reset user token',
        operation_description='Reset the user token for the current user.',
        request_body=no_body,
        responses={
            201: openapi.Response(
                description='User token response',
                schema=openapi.Schema(
                    description='User token',
                    type=openapi.TYPE_OBJECT,
                    properties={'token': openapi.Schema(description='Token', type=openapi.TYPE_STRING)},
                ),
            )
        },
    ),
)
class UserResetTokenAPI(APIView):
    parser_classes = (JSONParser, FormParser, MultiPartParser)
    queryset = User.objects.all()
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        user = request.user
        token = user.reset_token()
        logger.debug(f'New token for user {user.pk} is {token.key}')
        return Response({'token': token.key}, status=201)


@method_decorator(
    name='get',
    decorator=swagger_auto_schema(
        tags=['Users'],
        x_fern_sdk_group_name='users',
        x_fern_sdk_method_name='get_token',
        x_fern_audiences=['public'],
        operation_summary='Get user token',
        operation_description='Get a user token to authenticate to the API as the current user.',
        request_body=no_body,
        responses={
            200: openapi.Response(
                description='User token response',
                schema=openapi.Schema(
                    description='User token',
                    type=openapi.TYPE_OBJECT,
                    properties={'detail': openapi.Schema(description='Token', type=openapi.TYPE_STRING)},
                ),
            )
        },
    ),
)
class UserGetTokenAPI(APIView):
    parser_classes = (JSONParser,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        user = request.user
        token = Token.objects.get(user=user)
        return Response({'token': str(token)}, status=200)


@method_decorator(
    name='get',
    decorator=swagger_auto_schema(
        tags=['Users'],
        x_fern_sdk_group_name='users',
        x_fern_sdk_method_name='whoami',
        x_fern_audiences=['public'],
        operation_summary='Retrieve my user',
        operation_description='Retrieve details of the account that you are using to access the API.',
        request_body=no_body,
        responses={200: UserSerializer},
    ),
)
class UserWhoAmIAPI(generics.RetrieveAPIView):
    parser_classes = (JSONParser, FormParser, MultiPartParser)
    queryset = User.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

    def get(self, request, *args, **kwargs):
        return super(UserWhoAmIAPI, self).get(request, *args, **kwargs)


@method_decorator(
    name='patch',
    decorator=swagger_auto_schema(
        tags=['Users'],
        x_fern_sdk_group_name='users',
        x_fern_sdk_method_name='update_hotkeys',
        x_fern_audiences=['public'],
        operation_summary='Update user hotkeys',
        operation_description='Update the custom hotkeys configuration for the current user.',
        request_body=HotkeysSerializer,
        responses={200: HotkeysSerializer},
    ),
)
@method_decorator(
    name='get',
    decorator=swagger_auto_schema(
        tags=['Users'],
        x_fern_sdk_group_name='users',
        x_fern_sdk_method_name='get_hotkeys',
        x_fern_audiences=['public'],
        operation_summary='Get user hotkeys',
        operation_description='Retrieve the custom hotkeys configuration for the current user.',
        request_body=no_body,
        responses={200: HotkeysSerializer},
    ),
)
class UserHotkeysAPI(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, FormParser, MultiPartParser)

    def get(self, request, *args, **kwargs):
        """Retrieve the current user's hotkeys configuration"""
        try:
            user = request.user
            custom_hotkeys = user.custom_hotkeys or {}

            serializer = HotkeysSerializer(data={'custom_hotkeys': custom_hotkeys})
            if serializer.is_valid():
                return Response(serializer.validated_data, status=200)
            else:
                # If stored data is invalid, return empty config
                logger.warning(f'Invalid hotkeys data for user {user.pk}: {serializer.errors}')
                return Response({'custom_hotkeys': {}}, status=200)

        except Exception as e:
            logger.error(f'Error retrieving hotkeys for user {request.user.pk}: {str(e)}')
            return Response({'error': 'Failed to retrieve hotkeys configuration'}, status=500)

    def patch(self, request, *args, **kwargs):
        """Update the current user's hotkeys configuration"""
        try:
            serializer = HotkeysSerializer(data=request.data)

            if not serializer.is_valid():
                return Response({'error': 'Invalid hotkeys configuration', 'details': serializer.errors}, status=400)

            user = request.user

            # Security check: Ensure user can only update their own hotkeys
            if not user.is_authenticated:
                return Response({'error': 'Authentication required'}, status=401)

            # Update user's hotkeys
            user.custom_hotkeys = serializer.validated_data['custom_hotkeys']
            user.save(update_fields=['custom_hotkeys'])

            logger.info(f'Updated hotkeys for user {user.pk}')

            return Response(serializer.validated_data, status=200)

        except Exception as e:
            logger.error(f'Error updating hotkeys for user {request.user.pk}: {str(e)}')
            return Response({'error': 'Failed to update hotkeys configuration'}, status=500)
