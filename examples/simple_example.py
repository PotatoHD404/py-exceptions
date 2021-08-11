from pyexceptions import handle_exceptions


def divide(a, b):
    return a / b


@handle_exceptions
def main():
    i = 5
    j = 0
    c = divide(i, j)
    print(c)


if __name__ == '__main__':
    main()
