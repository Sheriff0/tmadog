package dog;

import org.json.JSONObject;

public class
FPuppy extends Puppy
{
    FPuppy(
	    String name,
	    String pwd,
	    Integer pid
	 )
	    throws AuthError
    {

	this(name, pwd, pid, null);
    }

    public FPuppy(JSONObject user)
	throws AuthError
    {
	this(user.getString(USR_ID), user.getString(USR_PWD), user.getInt(USR_PUPPY_ID));
    }

    FPuppy(
	    String name,
	    String pwd,
	    Integer pid,
	    FileServer server
	    )
	    throws AuthError
    {

	super(name, pwd, pid, (server == null)? new FileServer() : server);
    }

    public static Boolean
    user_exists(String name, String pwd)
    {
	init(new FileServer());
	FileServer serv = (FileServer)server;
	Boolean ne = serv.exists(name);
	JSONObject udata = load_user_rw(name);
	return ne && udata.has(USR_PWD) && pwd.compareTo(udata.getString(USR_PWD)) == 0;

    }


    public static Boolean
    user_exists(String name)
    {
	init(new FileServer());
	FileServer serv = (FileServer)server;
	return serv.exists(name);

    }


}
