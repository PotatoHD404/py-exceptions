# py-exceptions [![PyPI version](https://badge.fury.io/py/py-exception.svg)](https://badge.fury.io/py/py-exception)

## *A simple python exception reporter*

### Description

This library provides great stacktrace and
web request information like Django does
It can save it to html, return html to your code or
even response in AWS lambda format

The library nicely covers all your secret variables and
request data in it's report

### Screenshots

![Beautiful image](https://github.com/PotatoHD404/py-exceptions/blob/dev/image.jpg?raw=true)

## Quickstart

### Installation

```sh
pip install py-exception
```

### Simple example

Add decorator to function

```python
from pyexceptions import handle_exceptions

def devide(a, b):
    return a / b

@handle_exceptions
def main():
    i = 5
    j = 0
    c = devide(i, j)
    print(c)

if __name__ == '__main__':
    main()
```

You can also override folder for exception reports

```python
from pyexceptions import handle_exceptions

def devide(a, b):
    return a / b

@handle_exceptions(exceptions_floder='./SomeFolderPath')
def main():
    i = 5
    j = 0
    c = devide(i, j)
    print(c)

if __name__ == '__main__':
    main()
```

### AWS Lambda example

It is hard to determine what's went wrong when you are using
AWS lambda. So you can use the example not only to get full stacktrace
but to get lambda event and context information:

```python
from pyexceptions import handle_exceptions

@handle_exceptions(is_lambda=True)
def lambda_handler(event, context):
    message = f"Hello {event['first_name']} {event['last_name']}!"
    return { 
        'message' : message
    }
```

### Exclude from stacktrace

There may be situations when you don't want to see part of stacktrace

So if your application looks like this:

```python
from pyexceptions import handle_exceptions

def devide(a, b):
    return a / b

def real_main():
    i = 5
    j = 0
    c = devide(i, j)
    print(c)
    
def wrapper():
    real_main()

@handle_exceptions(exclude = 'exclude_example.wrapper')
def main():
    wrapper()

if __name__ == '__main__':
    main()
```

and you want to exclude all stacktrace from main to wrapper
you need to pass `file_name.function_name` as exclude argument

### Other functions

You can also want to use theese functions:

Make function that returns HTML:

```python
@handle_exceptions(return_html = True)
def main()
    ...
```

Or you may want to write your own logic
To do so you need to import the ExceptionHandler class

```python
from pyexceptions import ExceptionHandler
```

To be clear here how it looks like:

```python
class ExceptionHandler:
    """Organize and coordinate reporting on exceptions."""

    def __init__(self, lambda_event: dict = None, context: object=None, exclude: str=None):
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
```

## Attribution

This implementation draws upon work from:

- [Django](https://github.com/django/django)

- [vercel-python-wsgi](https://github.com/ardnt/vercel-python-wsgi)
