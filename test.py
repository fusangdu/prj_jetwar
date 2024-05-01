class A:
    def __init__(self,a,b):
        self.a=a
        self.b=b


class B(A):
    def __init__(self,a,b,c):
        super().__init__(a,b)
        self.c=c


b=B(1,2,3)
b.b