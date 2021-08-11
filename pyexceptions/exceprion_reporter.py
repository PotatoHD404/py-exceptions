import re
import os
import sys
import json
import base64
import logging
from io import BytesIO
from pathlib import Path
from functools import wraps
from datetime import datetime
from werkzeug.wrappers import Response
from urllib.parse import urlparse, unquote
from werkzeug.datastructures import Headers
from .jinja_changes import pprint, add, dictsort, force_escape
from werkzeug._internal import _wsgi_encoding_dance, _to_bytes  # noqa
from .safe_exception_handler import SafeExceptionReporterFilter
from jinja2 import Environment, select_autoescape, FileSystemLoader

PATH = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(PATH, 'templates')
print(PATH)
templateEnv = Environment(loader=FileSystemLoader(PATH),
                          autoescape=select_autoescape())

templateEnv.filters["pprint"] = pprint
templateEnv.filters["add"] = add
templateEnv.filters["dictsort"] = dictsort
templateEnv.filters['force_escape'] = force_escape

dt_string = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

'The class was taken from Django repository and edited by PotatoHD404'


class ExceptionReporter:
    """Organize and coordinate reporting on exceptions."""

    def __init__(self, lambda_event: dict = None, context=None, exclude=None):
        self.filter = SafeExceptionReporterFilter()
        self.context = context
        self.exclude = exclude
        self.exc_type, self.exc_value, self.tb = sys.exc_info()
        self.request = None
        if lambda_event is not None:
            event = json.loads(lambda_event['body'])
            headers = Headers(event.get('headers', None))
            parsed_url = urlparse(event['path'])

            body = event.get('body', '')
            encoding = event.get('encoding', None)

            if encoding == 'base64':
                body = base64.b64decode(body)
            else:
                body = _to_bytes(body, charset='utf-8')

            environ = {
                'CONTENT_LENGTH': str(len(body)),
                'CONTENT_TYPE': headers.get('content-type', ''),
                'PATH_INFO': parsed_url.path,
                'QUERY_STRING': unquote(parsed_url.query),
                'REMOTE_ADDR': event.get('x-real-ip', ''),
                'REQUEST_METHOD': event.get('method', 'GET'),
                'SCRIPT_NAME': '',
                'SERVER_NAME': headers.get('host', 'lambda'),
                'SERVER_PORT': headers.get('x-forwarded-port', '443'),
                'SERVER_PROTOCOL': 'HTTP/2',
                'wsgi.input': BytesIO(body).read().decode('utf-8'),
                'wsgi.multiprocess': False,
                'wsgi.multithread': False,
                'wsgi.run_once': False,
                'wsgi.url_scheme': headers.get('x-forwarded-proto', 'https'),
                'wsgi.version': (1, 0),
            }

            for key, value in environ.items():
                if isinstance(value, str):
                    environ[key] = _wsgi_encoding_dance(value)

            for key, value in headers.items():
                key = 'HTTP_' + key.upper().replace('-', '_')
                if key not in ('HTTP_CONTENT_TYPE', 'HTTP_CONTENT_LENGTH'):
                    environ[key] = value
            self.request = environ

    @staticmethod
    def _force_str(s, encoding='utf-8', errors='strict'):
        """
        Similar to smart_str(), except that lazy instances are resolved to
        strings, rather than kept as lazy objects.
        If strings_only is True, don't convert (some) non-string-like objects.
        """
        # Handle the common case first for performance reasons.
        if not issubclass(type(s), str):
            s = str(s, encoding, errors) if isinstance(s, bytes) else str(s)
        return s

    def _get_raw_insecure_uri(self):
        """
        Return an absolute URI from variables available in this request. Skip
        allowed hosts protection, so may return insecure URI.
        """
        return '{scheme}://{host}{path}'.format(
            scheme=self.request['wsgi.url_scheme'],
            host=self.request['SERVER_NAME'],
            path=self.request['PATH_INFO'],
            # scheme='https',
            # host='localhost',
            # path='/',
        )

    def get_traceback_data(self):
        """Return a dictionary containing traceback information."""

        frames = self.get_traceback_frames()
        for i, frame in enumerate(frames):
            if 'vars' in frame:
                frame_vars = []
                for k, v in frame['vars']:
                    v = pprint(v)
                    # Trim large blobs of data
                    if len(v) > 4096:
                        v = '%s… <trimmed %d bytes string>' % (v[0:4096],
                                                               len(v))
                    frame_vars.append((k, v))
                frame['vars'] = frame_vars
            frames[i] = frame

        unicode_hint = ''
        if self.exc_type and issubclass(self.exc_type, UnicodeError):
            start = getattr(self.exc_value, 'start', None)
            end = getattr(self.exc_value, 'end', None)
            if start is not None and end is not None:
                unicode_str = self.exc_value.args[1]
                unicode_hint = self._force_str(
                    unicode_str[max(start - 5, 0):min(end +
                                                      5, len(unicode_str))],
                    'ascii',
                    errors='replace')

        c = {
            'unicode_hint':
                unicode_hint,
            'frames':
                frames,
            'request':
                self.request,
            'request_meta':
                self.filter.get_safe_request_meta(self.request),
            'filtered_POST_items':
                list(self.filter.get_post_parameters(self.request).items()),
            'sys_executable':
                sys.executable,
            'sys_version_info':
                '%d.%d.%d' % sys.version_info[0:3],
            'server_time':
                dt_string,
            'sys_path':
                sys.path,
        }
        if self.request is not None:
            c['request_GET_items'] = self.request['GET'].items()
            c['request_FILES_items'] = self.request['FILES'].items()
            c['request_COOKIES_items'] = self.request['COOKIES'].items()
            c['request_insecure_uri'] = self._get_raw_insecure_uri()

        # Check whether exception info is available
        if self.exc_type:
            c['exception_type'] = self.exc_type.__name__
        if self.exc_value:
            c['exception_value'] = str(self.exc_value)
        if frames:
            c['lastframe'] = frames[-1]
        return c

    def get_traceback_html(self):
        """Return HTML version of debug 500 HTTP error page."""

        t = templateEnv.get_template('500.html')
        c = self.get_traceback_data()
        return t.render(**c)

    def get_lambda_response(self):
        response = Response(self.get_traceback_html(), mimetype='text/html')
        headers = {}
        for key, value in response.headers:
            if key in headers:
                current_value = headers[key]
                if isinstance(current_value, list):
                    headers[key] += [value]
                else:
                    headers[key] = [current_value, value]
            else:
                headers[key] = value

        returndict = {
            'statusCode': response.status_code,
            'headers': headers,
            'body': '',
        }
        if response.data:
            mimetype = response.mimetype or 'text/plain'
            text_mime_types = [
                'application/json',
                'application/javascript',
                'application/xml',
                'application/vnd.api+json',
                'image/svg+xml']
            if (mimetype.startswith('text/') or mimetype in text_mime_types) and not response.headers.get(
                    'Content-Encoding', ''):
                returndict['body'] = response.get_data(as_text=True)
            else:
                returndict['body'] = base64.b64encode(
                    response.data).decode('utf-8')
                returndict['encoding'] = 'base64'
        return returndict

    @staticmethod
    def _get_source(filename, loader, module_name):
        source = None
        if hasattr(loader, 'get_source'):
            try:
                source = loader.get_source(module_name)
            except ImportError:
                pass
            if source is not None:
                source = source.splitlines()
        if source is None:
            try:
                with open(filename, 'rb') as fp:
                    source = fp.read().splitlines()
            except OSError:
                pass
        return source

    def _get_lines_from_file(self,
                             filename,
                             lineno,
                             context_lines,
                             loader=None,
                             module_name=None):
        """
        Return context_lines before and after lineno from file.
        Return (pre_context_lineno, pre_context, context_line, post_context).
        """
        source = self._get_source(filename, loader, module_name)
        if source is None:
            return None, [], None, []

        # If we just read the source from a file, or if the loader did not
        # apply tokenize.detect_encoding to decode the source into a
        # string, then we should do that ourselves.
        if isinstance(source[0], bytes):
            encoding = 'ascii'
            for line in source[:2]:
                # File coding may be specified. Match pattern from PEP-263
                # (https://www.python.org/dev/peps/pep-0263/)
                match = re.search(br'coding[:=]\s*([-\w.]+)', line)
                if match:
                    encoding = match[1].decode('ascii')
                    break
            source = [str(sline, encoding, 'replace') for sline in source]

        lower_bound = max(0, lineno - context_lines)
        upper_bound = lineno + context_lines

        try:
            pre_context = source[lower_bound:lineno]
            context_line = source[lineno]
            post_context = source[lineno + 1:upper_bound]
        except IndexError:
            return None, [], None, []
        return lower_bound, pre_context, context_line, post_context

    @staticmethod
    def _get_explicit_or_implicit_cause(exc_value):
        explicit = getattr(exc_value, '__cause__', None)
        suppress_context = getattr(exc_value, '__suppress_context__', None)
        implicit = getattr(exc_value, '__context__', None)
        return explicit or (None if suppress_context else implicit)

    def get_traceback_frames(self):
        # Get the exception and all its causes
        exceptions = []
        exc_value = self.exc_value
        while exc_value:
            exceptions.append(exc_value)
            exc_value = self._get_explicit_or_implicit_cause(exc_value)
            if exc_value in exceptions:
                # Avoid infinite loop if there's a cyclic reference (#29393).
                break

        frames = []
        # No exceptions were supplied to ExceptionReporter
        if not exceptions:
            return frames

        # In case there's just one exception, take the traceback from self.tb
        exc_value = exceptions.pop()
        tb = self.tb if not exceptions else exc_value.__traceback__
        while True:
            frames.extend(self.get_exception_traceback_frames(exc_value, tb))
            try:
                exc_value = exceptions.pop()
            except IndexError:
                break
            tb = exc_value.__traceback__
        return frames

    def get_exception_traceback_frames(self, exc_value, tb):
        exc_cause = self._get_explicit_or_implicit_cause(exc_value)
        exc_cause_explicit = getattr(exc_value, '__cause__', True)
        if tb is None:
            yield {
                'exc_cause': exc_cause,
                'exc_cause_explicit': exc_cause_explicit,
                'tb': None,
                'type': 'user',
            }
        while tb is not None:
            # Support for __traceback_hide__ which is used by a few libraries
            # to hide internal frames.
            if tb.tb_frame.f_locals.get('__traceback_hide__'):
                tb = tb.tb_next
                continue
            filename = tb.tb_frame.f_code.co_filename
            function = tb.tb_frame.f_code.co_name
            lineno = tb.tb_lineno - 1
            loader = tb.tb_frame.f_globals.get('__loader__')
            module_name = tb.tb_frame.f_globals.get('__name__') or ''
            pre_context_lineno, pre_context, context_line, post_context = self._get_lines_from_file(
                filename,
                lineno,
                7,
                loader,
                module_name,
            )
            if pre_context_lineno is None:
                pre_context_lineno = lineno
                pre_context = []
                context_line = '<source code not available>'
                post_context = []
            yield {
                'exc_cause':
                    exc_cause,
                'exc_cause_explicit':
                    exc_cause_explicit,
                'tb':
                    tb,
                'type':
                    'django' if module_name.startswith('django.') else 'user',
                'filename':
                    filename,
                'function':
                    function,
                'lineno':
                    lineno + 1,
                'vars':
                    self.filter.get_traceback_frame_variables(
                        self.request, tb.tb_frame),
                'id':
                    id(tb),
                'pre_context':
                    pre_context,
                'context_line':
                    context_line,
                'post_context':
                    post_context,
                'pre_context_lineno':
                    pre_context_lineno + 1,
            }
            tb = tb.tb_next


class ExceptionHandler:
    """Organize and coordinate reporting on exceptions."""

    def __init__(self, lambda_event: dict = None, context: object = None, exclude: str = None):
        """Exception reporter initializer

        Args:
            lambda_event (dict, optional): AWS lambda event. Defaults to None.
            context (object, optional): AWS lambda context. Defaults to None.
            exclude (str, optional): Function to exclude Defaults to None.

        """
        self.__reporter = ExceptionReporter(lambda_event, context, exclude)

    def get_traceback_html(self):
        """Return HTML version of debug 500 HTTP error page."""
        return self.__reporter.get_traceback_html()

    def get_traceback_lambda(self):
        """Return AWS lambda version of debug 500 HTTP error page."""
        return self.__reporter.get_lambda_response()


def handle_exceptions(function=None, is_lambda: bool = False, return_html: bool = False,
                      exceptions_folder: str = None, exclude: str = None, only_last: bool = True):
    """Organize and coordinate reporting on exceptions.

    Args:
        function
        is_lambda (bool, optional): Set true if you want to handle lambda function. Defaults to False.
        return_html (bool, optional): Set true if you want the function to return html. Defaults to False.
        exceptions_folder (str, optional): Sets the exceptions folder. Defaults to None.
        exclude (str, optional): Determines which part of stacktrace to exclude. Defaults to None.
        only_last (bool, optional): Determines whether only last report should be saved. Defaults to True.

    Raises:
        OSError: If file was not written correctly this error will raise
    """

    @wraps(function)
    def wrapper(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except Exception:  # noqa
            if is_lambda:
                return ExceptionHandler(exclude=exclude).get_traceback_lambda()
            elif return_html:
                return ExceptionHandler(exclude=exclude).get_traceback_html()
            else:
                return save_exception(ExceptionHandler(exclude=exclude).get_traceback_html(), exceptions_folder)

    def save_exception(html, exceptions_folder):  # noqa
        time_string = datetime.now().strftime(r"%d-%m-%Y_%H-%M-%S")
        file_name = f'handled_exception_{time_string}.html'
        if exceptions_folder is None:
            exceptions_folder = os.path.dirname(os.path.abspath(__file__))  # noqa
            exceptions_folder = os.path.join(exceptions_folder, 'handled_exceptions')  # noqa
        Path(exceptions_folder).mkdir(parents=True, exist_ok=True)
        if only_last:
            files_in_directory = os.listdir(exceptions_folder)
            filtered_files = [file for file in files_in_directory if file.endswith(".html")]
            for file in filtered_files:
                path_to_file = os.path.join(exceptions_folder, file)
                os.remove(path_to_file)
        file_path = os.path.join(exceptions_folder, file_name)
        try:
            with open(file_path, "w") as f:
                f.write(html)
            logging.warning(f'Handled exception: \nfile://{file_path}')
        except Exception as e:
            raise OSError('Failed to save file while handling exception: \n' + str(e))
        return None

    return wrapper
