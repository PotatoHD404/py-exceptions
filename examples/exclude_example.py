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