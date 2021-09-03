package dog;

import org.json.JSONObject;

public class
FPuppy extends Puppy
{
    private static final Server serv = new FileServer();

    public FPuppy(JSONObject user)
	throws AuthError
    {
	this(user.getString(USR_ID), user.getString(USR_PWD), user.getInt(USR_PUPPY_ID));
    }

    FPuppy(
	    String name,
	    String pwd,
	    Integer pid
	    )
	    throws AuthError
    {

	super(name, pwd, pid, serv);
    }

    public static Boolean
    user_exists(String name, String pwd)
    {
	Boolean ne = serv.exists(name);
	JSONObject udata = load_user_rw(name);
	return ne && udata.has(USR_PWD) && pwd.compareTo(udata.getString(USR_PWD)) == 0;

    }


    public static Boolean
    user_exists(String name)
    {
	return serv.exists(name);

    }


}
