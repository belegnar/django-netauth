from django.conf import settings as global_settings
from django.utils import simplejson
from django.utils.datastructures import MultiValueDictKeyError
from oauth2 import Consumer, Token, Request, SignatureMethod_HMAC_SHA1

from netauth.backends import OAuthBaseBackend
from netauth.exceptions import Redirect


class OAuthBackend(OAuthBaseBackend):

    CONSUMER_KEY = property(lambda self: getattr(global_settings, "%s_CONSUMER_KEY" % self.provider.upper()))
    CONSUMER_SECRET = property(lambda self: getattr(global_settings, "%s_CONSUMER_SECRET" % self.provider.upper()))
    REQUEST_TOKEN_URL = property(lambda self: getattr(global_settings, "%s_REQUEST_TOKEN_URL" % self.provider.upper()))

    def __init__( self, *args, **kwargs ):
        super( OAuthBackend, self ).__init__( *args, **kwargs )
        self.consumer = Consumer(self.CONSUMER_KEY, self.CONSUMER_SECRET)
        self.signature_method = SignatureMethod_HMAC_SHA1()

    def begin(self, request, data):
        """ Try to get Request Token from OAuth Provider and
            redirect user to provider's site for approval.
        """
        request = self.get_request( http_url=self.REQUEST_TOKEN_URL,
                parameters = {'oauth_callback':self.callback( request )})
        content = self.load_request(request)
        request = self.get_request( token = Token.from_string(content), http_url=self.AUTHORIZE_URL,)
        raise Redirect(request.to_url())

    def validate(self, request, data):
        try:
            parameters = dict(oauth_token = data['oauth_token'], oauth_verifier = data.get('oauth_verifier', None))
        except MultiValueDictKeyError:
            self.error()

        request = self.get_request( http_url=self.ACCESS_TOKEN_URL, parameters=parameters)
        content = self.load_request(request)
        self.identity = self.parse_qs(content)['oauth_token'][0]
        return content

    def get_extra_data(self, response):
        user_id = self.parse_qs(response)['user_id'][0]
        request = super( OAuthBackend, self ).get_request( self.API_URL % user_id )
        content = self.load_request(request)
        return simplejson.loads(content)

    def extract_data(self, extra, backend_field, form_field):
        return {form_field: extra.get(backend_field, '')}

    def get_request( self, token=None, http_url=None, parameters=dict() ):
        request = Request.from_consumer_and_token( self.consumer, token = token,
                    http_url=http_url, parameters=parameters)
        request.sign_request(self.signature_method, self.consumer, token)
        return request
