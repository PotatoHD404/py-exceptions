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