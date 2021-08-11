import re
from .multi_value_dict import MultiValueDict

'The classes was taken from Django repository and edited by PotatoHD404'


class CallableSettingWrapper:
    """
    Object to wrap callable appearing in settings.
    * Not to call in the debug page (#21345).
    * Not to break the debug page if the callable forbidding to set attributes
      (#23070).
    """

    def __init__(self, callable_setting):
        self._wrapped = callable_setting

    def __repr__(self):
        return repr(self._wrapped)


class SafeExceptionReporterFilter:
    """
    Use annotations made by the sensitive_post_parameters and
    sensitive_variables decorators to filter out sensitive information.
    """
    cleansed_substitute = '********************'
    hidden_settings = re.compile('API|TOKEN|KEY|SECRET|PASS|SIGNATURE',
                                 flags=re.I)

    def cleanse_setting(self, key, value):
        """
        Cleanse an individual setting key/value of sensitive content. If the
        value is a dictionary, recursively cleanse the keys in that dictionary.
        """
        try:
            is_sensitive = self.hidden_settings.search(key)
        except TypeError:
            is_sensitive = False

        if is_sensitive:
            cleansed = self.cleansed_substitute
        elif isinstance(value, dict):
            cleansed = {
                k: self.cleanse_setting(k, v)
                for k, v in value.items()
            }
        elif isinstance(value, list):
            cleansed = [self.cleanse_setting('', v) for v in value]
        elif isinstance(value, tuple):
            cleansed = tuple(self.cleanse_setting('', v) for v in value)
        else:
            cleansed = value

        if callable(cleansed):
            cleansed = CallableSettingWrapper(cleansed)

        return cleansed

    def get_safe_request_meta(self, request):
        """
        Return a dictionary of request.META with sensitive values redacted.
        """
        if request is None:
            return {}

        return {k: self.cleanse_setting(k, v) for k, v in request.items()}

    def get_cleansed_multivaluedict(self, request, multivaluedict):
        """
        Replace the keys in a MultiValueDict marked as sensitive with stars.
        This mitigates leaking sensitive POST parameters if something like
        request.POST['nonexistent_key'] throws an exception (#21098).
        """
        sensitive_post_parameters = getattr(request,
                                            'sensitive_post_parameters', [])
        if sensitive_post_parameters:
            multivaluedict = multivaluedict.copy()
            for param in sensitive_post_parameters:
                if param in multivaluedict:
                    multivaluedict[param] = self.cleansed_substitute
        return multivaluedict

    def get_post_parameters(self, request):
        """
        Replace the values of POST parameters marked as sensitive with
        stars (*********).
        """
        if request is None:
            return {}
        sensitive_post_parameters = getattr(request,
                                            'sensitive_post_parameters', [])
        if not sensitive_post_parameters:
            # return request.POST
            return {}

        cleansed = request.POST.copy()
        if sensitive_post_parameters == '__ALL__':
            # Cleanse all parameters.
            for k in cleansed:
                cleansed[k] = self.cleansed_substitute
        else:
            # Cleanse only the specified parameters.
            for param in sensitive_post_parameters:
                if param in cleansed:
                    cleansed[param] = self.cleansed_substitute
        return cleansed

    def cleanse_special_types(self, request, value):
        try:
            # If value is lazy or a complex object of another kind, this check
            # might raise an exception. isinstance checks that lazy
            # MultiValueDicts will have a return value.
            is_multivalue_dict = isinstance(value, MultiValueDict)
        except Exception as e:
            return '{!r} while evaluating {!r}'.format(e, value)

        if is_multivalue_dict:
            # Cleanse MultiValueDicts (request.POST is the one we usually care about)
            value = self.get_cleansed_multivaluedict(request, value)
        return value

    def get_traceback_frame_variables(self, request, tb_frame):
        """
        Replace the values of variables marked as sensitive with
        stars (*********).
        """
        # Loop through the frame's callers to see if the sensitive_variables
        # decorator was used.
        current_frame = tb_frame.f_back
        sensitive_variables = None
        while current_frame is not None:
            if (current_frame.f_code.co_name == 'sensitive_variables_wrapper'
                    and 'sensitive_variables_wrapper'
                    in current_frame.f_locals):
                # The sensitive_variables decorator was used, so we take note
                # of the sensitive variables' names.
                wrapper = current_frame.f_locals['sensitive_variables_wrapper']
                sensitive_variables = getattr(wrapper, 'sensitive_variables',
                                              None)
                break
            current_frame = current_frame.f_back

        cleansed = {}
        if sensitive_variables:
            if sensitive_variables == '__ALL__':
                # Cleanse all variables
                for name in tb_frame.f_locals:
                    cleansed[name] = self.cleansed_substitute
            else:
                # Cleanse specified variables
                for name, value in tb_frame.f_locals.items():
                    if name in sensitive_variables:
                        value = self.cleansed_substitute
                    else:
                        value = self.cleanse_special_types(request, value)
                    cleansed[name] = value
        else:
            # Potentially cleanse the request and any MultiValueDicts if they
            # are one of the frame variables.
            for name, value in tb_frame.f_locals.items():
                cleansed[name] = self.cleanse_special_types(request, value)

        if (tb_frame.f_code.co_name == 'sensitive_variables_wrapper'
                and 'sensitive_variables_wrapper' in tb_frame.f_locals):
            # For good measure, obfuscate the decorated function's arguments in
            # the sensitive_variables decorator's frame, in case the variables
            # associated with those arguments were meant to be obfuscated from
            # the decorated function's frame.
            cleansed['func_args'] = self.cleansed_substitute
            cleansed['func_kwargs'] = self.cleansed_substitute

        return cleansed.items()
