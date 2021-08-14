package dog;

class User
{
    final byte
	STARTED = 0b01,
	DIRTY = 0b10;

    Resu status;

    private org.json.JSONObject _data;

    private String _name;

    private Server _server;
    
    byte _flags;

    boolean _init()
    {
	if(STARTED & _flags > 0)
	    return true;

	_flags = 0;

	// NOTE: error handling
	_data = _server.readFileJSON(_name);

	return true;
    }

    User(String name)
    {
	_name = name;
	_server = new Dropbox();
    }

    User(Server server)
    {
	_server = server;

	// An implicit name
	_name = null;
    }

    User(String name, Server server)
    { 
	_name = name;
	_server = server;
    }

    <JSONType> JSONType get(String key)
    {
	if(_init())
	    JSONType res = _data.get(key);
	else
	    JSONType res = new T();

	return res;
    }

    <JSONType> boolean set(String key, JSONType value)
    {
	if(_init())
	{
	    JSONType res = _data.put(key);
	    _flags |= DIRTY;

	} else
	    return false;

	return true;
    }

    boolean flush(boolean force)
    {
	if(!(_init()))
	    return false;

	if((_flags & DIRTY) == 0) // clean
	{
	    if(!force)
		return true;
	}

	return _sync();
	
    }

    boolean _sync()
    {

    }

    String toString(){ return _name; };

}
