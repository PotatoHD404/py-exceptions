from pyexceptions import handle_exceptions


def divide(a, b):
    return a / b


def real_main():
    i = 5
    j = 0
    c = divide(i, j)
    print(c)


def wrapper():
    real_main()


@handle_exceptions(exclude=2)
def main():
    wrapper()


if __name__ == '__main__':
    main()
