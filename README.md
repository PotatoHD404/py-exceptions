# py-exceptions

## *A simple python exception reporter*

[![NPM version](https://img.shields.io/npm/v/@potatohd/vercel-package-installer.svg)](https://pypi.org/project/py-extensions/)

## Quickstart

If you have an existing WSGI app, getting this builder to work for you is a
piece of 🍰!

### 1. Add a Vercel configuration

Add a `vercel.json` file to the root of your application:

```json
{
    "builds": [{
        "src": "index.py",
        "use": "@potatohd/vercel-package-installer1",
        "config": { "maxLambdaSize": "15mb" }
    }]
}
```

This configuration is doing a few things in the `"builds"` part:

1. `"src": "index.py"`
   This tells Now that there is one entrypoint to build for. `index.py` is a
   file we'll create shortly.
2. `"use": "@potatohd/vercel-package-installer1"`
   Tell Now to use this builder when deploying your application
3. `"config": { "maxLambdaSize": "15mb" }`
   Bump up the maximum size of the built application to accommodate some larger
   python WSGI libraries (like Django or Flask). This may not be necessary for
   you.

### 2. Add a Now entrypoint

Add `index.py` to the root of your application. This entrypoint should make
available an object named `application` that is an instance of your WSGI
application. E.g.:

```python
# For a Dango app
from django_app.wsgi import application
# Replace `django_app` with the appropriate name to point towards your project's
# wsgi.py file
```

Look at your framework documentation for help getting access to the WSGI
application.

If the WSGI instance isn't named `application` you can set the
`wsgiApplicationName` configuration option to match your application's name (see
the configuration section below).

### 3. Deploy

That's it, you're ready to go:

```console
$ vercel
> Deploying python-wsgi-app
...
> Success! Deployment ready [57s]
```

### Avoiding the `index.py` file

If having an extra file in your project is troublesome or seems unecessary, it's
also possible to configure Now to use your application directly, without passing
it through `index.py`.

If your WSGI application lives in `vercel_app/wsgi.py` and is named `application`,
then you can configure it as the entrypoint and adjust routes accordingly:

```json
{
    "builds": [{
        "src": "vercel_app/wsgi.py",
        "use": "@potatohd/vercel-package-installer"
    }],
    "routes" : [{
        "src" : "/(.*)", "dest":"/vercel_app/wsgi.py"
    }]
}
```

## Attribution

This implementation draws upon work from:

- [Django](https://github.com/django/django)

- [vercel-python-wsgi](https://github.com/ardnt/vercel-python-wsgi)
