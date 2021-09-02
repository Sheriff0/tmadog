package dog;

abstract class
Server
{
    abstract public String get(String path);

    abstract public Integer put(String path, String data);

    abstract public Integer post(String path, String data);
    abstract public Boolean exists(String path);
}
