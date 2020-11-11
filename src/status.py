import io

class StatusBuffer(io.StringIO):
    def __init__(self, cline = "#", *pargs, **kwargs):
        """cline is an internal line delimiter - this is useful to ease the
        one, status, one, line restrictionand support
        command whose verbose output for a single status span multiple lines"""
        self.cline = cline;



S_NULL = 0;
S_ERROR = 0b0001;
S_INT = 0b0010;
S_OK = 0b0100;
S_MASK = 0b1111;

class UnknownStatus(BaseException):
    def __init__(self, *pargs, *kwargs):
        super ().__init__ (*pargs, **kwargs);


class Status:
    def __init__(self, code = S_NULL, msg = None, cause = None):
        if code != S_NULL and code & S_MASK:
            raise UnknownStatus(code);
        self.code = code;
        self.msg = msg;
        self.cause = cause;

    def __bool__(self):
        return self.code == S_OK;
