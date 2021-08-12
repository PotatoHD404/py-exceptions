from pyexceptions import handle_exceptions


@handle_exceptions(is_lambda=True)
def lambda_handler(event, context):
    message = f"Hello {event['first_name']} {event['last_name']}!"
    return {
        'message': message
    }


if __name__ == '__main__':
    print(lambda_handler({'body': '{"method":"GET","headers":{"host":"vercel-test-dmwsbpjtj-potatohd.vercel.app","x-real-ip":"127.0.0.1","sec-fetch-user":"?1","sec-ch-ua-mobile":"?0","sec-fetch-site":"cross-site","upgrade-insecure-requests":"1","referer":"https:\\/\\/vercel.com\\/","x-vercel-forwarded-for":"127.0.0.1","sec-ch-ua":"\\"Chromium\\";v=\\"92\\", \\" Not A;Brand\\";v=\\"99\\", \\"Google Chrome\\";v=\\"92\\"","x-vercel-id":"arn1::rnqhk-1628774674261-fc764e70949f","x-forwarded-host":"vercel-test-dmwsbpjtj-potatohd.vercel.app","accept":"text\\/html,application\\/xhtml+xml,application\\/xml;q=0.9,image\\/avif,image\\/webp,image\\/apng,*\\/*;q=0.8,application\\/signed-exchange;v=b3;q=0.9","x-vercel-deployment-url":"vercel-test-dmwsbpjtj-potatohd.vercel.app","x-forwarded-for":"127.0.0.1","x-forwarded-proto":"https","sec-fetch-mode":"navigate","accept-encoding":"gzip, deflate, br","user-agent":"Mozilla\\/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit\\/537.36 (KHTML, like Gecko) Chrome\\/92.0.4515.131 Safari\\/537.36","accept-language":"ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7","sec-fetch-dest":"document"},"path":"\\/","host":"vercel-test-dmwsbpjtj-potatohd.vercel.app"}', 'Action': 'Invoke'}, None))
