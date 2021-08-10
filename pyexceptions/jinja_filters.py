from pprint import pformat

def pprint(value):
	"""A wrapper around pprint.pprint -- for debugging, really."""
	try:
		return pformat(value)
	except Exception as e:
		return "Error in formatting: %s: %s" % (e.__class__.__name__, e)
