package dog;

class User
{
    final byte
	STARTED = 0b01,
	DIRTY = 0b10;

    Resu status;

    private String _name;

    private Server _server;

    byte _flags;

    protected org.json.JSONObject _data;

    private boolean
    _init()
    {
	if(STARTED & this._flags > 0)
	    return true;

	this._server = new Dropbox();

	// NOTE: error handling
	update(_server.readFileJSON(this._name));

	this.status = Resu(this.toString());

	sync();

	return true;
    }
    
    User()
    {
	super();
	this._flags = 0;
	this._data = new org.json.JSONObject();
    }

    User(String name)
    {
	this();
	this._name = name;
    }

    User(Server server)
    {
	this();
	this._server = server;

    }

    User(String name, Server server)
    { 
	super();
	this._name = name;
	this._server = server;
    }

    void set_dirty() { this._flags |= DIRTY; };

    <JSONType> boolean
    set(String key, JSONType value)
    {
	if(_init())
	{
	    set_dirty();
	    this._data.put(key, value);

	} else
	    return false;

	return true;
    }

    boolean
    flush(boolean force)
    {
	if(!(_init()))
	    return false;

	if((this._flags & DIRTY) == 0) // clean
	{
	    if(!force)
		return true;
	}

	return this._server.writeFileJSON(_name, this._data);

    }

    boolean
    sync()
    {
	if(!(_init()))
	    return false;

	return this.status.sync();
    }
    
    // shallow copy
    boolean 
    update(<? extends org.json.JSONObject> other)
    {
	for(String key : other.keySet())
	{
	    this.put(key, other.get(key));
	}

	return true;
    }

    boolean 
    copy(<? extends User> other)
    {
	for(String key : other.keySet())
	{
	    this.put(key, other.get(key));
	}

	return true;
    }

    String toString(){ return this._name; };

    // overides
    

    public int length() { return this._data.length(); };
    public void
    clear()
    {
	set_dirty();
	this._data.clear();
    }

    public boolean isEmpty() { return this._data.isEmpty(); };

    
    public Iterator<String> keys() { return keySet().iterator(); };

    Set
    keySet()
    {
	return this._data.keySet().clone(); 
    }

    <JSONType> JSONType
    get(String key)
    {
	if(!(_init()))
	    return new JSONType();

	return super.get(key);
    }


    <JSONType> boolean
    put(String key, JSONType value)
    {
	return set<JSONType>(key, value);
    }

    public void
    clear()
    {
	set_dirty();
	return super.clear();
    }

    public Object
    remove(String key)
    {
	this.set_dirty();
	return super.remove(key);
    }

}
