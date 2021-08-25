package dog;

abstract class
Server
{
    abstract String get(String path);
    abstract String put(String path, String data);
    abstract String post(String path, String data);
}
