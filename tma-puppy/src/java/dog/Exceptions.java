class
AuthError extends Exception {};


class
NoFileNoCreate extends IOException {};

class
NoDirNoRead extends IOException {};


class
Errno extends Exception
{
    static Exception errno;
}
