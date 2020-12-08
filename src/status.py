S_NULL = 0;
S_OK = 0b0001;
S_INT = 0b0010;
S_ERROR = 0b0100;
S_FATAL = 0b1000;
S_MASK = 0b1111;

class UnknownStatus(BaseException):
    def __init__(self, *pargs, **kwargs):
        super ().__init__ (*pargs, **kwargs);


class Status:
    def __init__(self, code = S_NULL, msg = "", cause = None):
        if code != S_NULL and not (code & S_MASK):
            raise UnknownStatus(code);
        self.code = code;
        self.msg = msg;
        self.cause = cause;

    def __bool__(self):
        return self.code == S_OK;
