# -*- coding: utf-8 -*-

import colander

from h import i18n
from h.models.auth_client import GrantType, ResponseType
from h.schemas.base import CSRFSchema, enum_type

_ = i18n.TranslationString
GrantTypeSchemaType = enum_type(GrantType)
ResponseTypeSchemaType = enum_type(ResponseType)


class CreateAuthClientSchema(CSRFSchema):
    name = colander.SchemaNode(
             colander.String(),
             title=_('Name'),
             hint=_('This will be displayed to users in the '
                    'authorization prompt'))

    authority = colander.SchemaNode(
                  colander.String(),
                  title=_('Authority'),
                  hint=_('Set of users whose data this client '
                         'can interact with'))

    grant_type = colander.SchemaNode(GrantTypeSchemaType(),
                                     title=_('Grant type'),
                                     hint=_('This specifies what type of authentication is used'))

    response_type = colander.SchemaNode(ResponseTypeSchemaType(),
                                        title=_('Response type'),
                                        hint=_('Specifies what kind of authorization response '
                                               'is returned to the client'))

    trusted = colander.SchemaNode(
                colander.Boolean(),
                title=_('Trusted'),
                hint=_('Trusted clients do not require user approval'))

    redirect_url = colander.SchemaNode(
                     colander.String(),
                     missing=None,
                     title=_('Redirect URL'),
                     hint=_('The browser will redirect to this URL after '
                            'authorization'))


class EditAuthClientSchema(CreateAuthClientSchema):

    # Read-only fields, listed in the form so that the user can easily copy and
    # paste them into their client's configuration.

    client_id = colander.SchemaNode(
                  colander.String(),
                  title=_('Client ID'))

    client_secret = colander.SchemaNode(
                      colander.String(),
                      missing=None,
                      title=_('Client secret'))
