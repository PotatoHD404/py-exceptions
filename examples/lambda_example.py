from pyexceptions import handle_exceptions


@handle_exceptions(is_lambda=True)
def lambda_handler(event, context):
    message = f"Hello {event['first_name']} {event['last_name']}!"
    return {
        'message': message
    }


if __name__ == '__main__':
    print(lambda_handler())
