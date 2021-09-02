package dog;

/* ======================= 
 * Data managed by a puppy
 * =======================
 *
 * Basic Structures
 * ================
 *
 * - crsobj:
 *   name(string): unique case-insensitive id. Can be the keyword 'all'.
 *
 *   status(string):
 *
 *
 * - user: This is the core data structure a puppy(as well as a dog) will manage they have the following properties:
 * 	id(string): 
 * 		a case-insensitive unique id.
 * 	pwd(string):
 * 		a case-sensitive password.
 * 	
 * 	crscode(object):
 * 		a collection of *crsobj* objects with unique access keys.
 * 	
 * Files
 * =====
 * One data will be in a read/write file uniquely named with
 * an *id*. Only one puppy can be *assigned* a
 * single file at any particular point in time.
 * The file will contain the following
 * structures:
 * 	id(string): same as the filename.
 *
 * 	pwd(string):
 * 		This is set once on file creation. It provides minimal access control and it's case sensitive.
 *
 * 	assigned(boolean):
 * 		Whether or not a puppy is already assigned.
 *
 * 	load(object):
 * 		lcount(int): A unique number incremented for any new load.
 *
 * 		data(object): A collection of *user* objects.
 *
 * Another corresponding data will be in a
 * read-only file uniquely named by reversing
 * preceding filename, e.g from 'id123' to
 * '321di'. This file is created by a dog. It is
 * read by a puppy to display info of a user
 * (like slots, load status etc). It contains to following:
 * 	
 * 	lcount(int): The last lcount processed above.
 *
 * 	trace(object): A collection of *user* objects.
 *
 * 	journal(object): for use by a dog.
 *
 *
 */


import java.util.Vector;
import java.io.BufferedReader;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.ArrayList;
import java.nio.file.Path;
import java.nio.file.FileSystems;
import java.nio.file.Files;
import java.io.IOException;
import java.util.Set;
import java.io.File;
import java.lang.Iterable;
import java.util.Map;


import net.sourceforge.argparse4j.ArgumentParsers;
import net.sourceforge.argparse4j.inf.ArgumentParser;
import net.sourceforge.argparse4j.inf.Namespace;

import net.sourceforge.argparse4j.internal.UnrecognizedArgumentException;
import net.sourceforge.argparse4j.inf.ArgumentParserException;

import org.json.JSONObject;
import org.json.JSONArray;
import org.json.JSONException;

abstract public class 
Puppy
{
    private static byte flags = 0;
    
    private static final byte
	F_INIT = 0b0001;


    public static final String
	MSG_INVALID_PID = "User already logged-in another device",
	MSG_INVALID_NAME = "Invalid Username",
	MSG_INVALID_PWD = "Invalid password";
    
    public static final byte
	NULL_ID = 0,
	NO_SLOT = 0,
	MIN_SLOT = 1;
    
    public static final byte INIT_MAX_PID = 10;

    public static final String
	USR_ID = "uid",
	USR_PWD = "pwd",
	USR_TRANSACTION_ID = "tid",
	USR_TRANSACTION = "tranc",
	USR_PUPPY_ID = "pid",
	USR_EXTRAS = "extras",
	USR_CRSCODES = "courses",
	USR_SLOTS = "slots",

	// for jobs
	USR_JOB_CMDLINE = "cmdline",
	USR_JOB_NAME = "name";
    


    private final JSONObject user_rw;

    private JSONObject user_r;

    public final String
	name,
	name_r,
	pwd;
    
    protected static Server server;

    //Puppy id
    public final Integer pid;


    Puppy(
	    String name,
	    String pwd,
	    Integer pid
	 )
	throws AuthError
    {
	this(name, pwd, pid, null);
    }

    Puppy(JSONObject user)
	throws AuthError
    {
	this(user.getString(USR_ID),
		user.getString(USR_PWD),
		user.getInt(USR_PUPPY_ID));
    }

    Puppy(
	    String name,
	    String pwd,
	    Integer pid,
	    Server server
	    )
	    throws AuthError
    {
	init(server);

	JSONObject user_rw = load_user_rw(name);

	if (is_user_rw_empty(user_rw))
	{
	    user_rw = init_new_user(name, pwd, user_rw);
	    pid = user_rw.getInt(USR_PUPPY_ID);

	} else
	{

	    if(name.compareTo(user_rw.getString(USR_ID)) != 0)
		throw new AuthError(
			MSG_INVALID_NAME + String.format(" %s", name));


	    if(pwd.compareTo(user_rw.getString(USR_PWD)) != 0)
		throw new AuthError(
			MSG_INVALID_PWD + String.format(" %s", pwd));

	    if(user_rw.getInt(USR_PUPPY_ID) == NULL_ID)
	    {
		pid = get_new_pid();
		user_rw.put(USR_PUPPY_ID, pid);

	    }else if(pid != user_rw.getInt(USR_PUPPY_ID))
		throw new AuthError(MSG_INVALID_PID);
	}

	this.name = name;
	this.pwd = pwd;
	this.pid = pid;

	this.user_rw = user_rw;
	
	this.name_r = to_name_r(name);

	this.user_r = load_user_r(this.name_r);


    }

    // must be called for some critical operations where a server or parser is needed. 
    protected static boolean
    init(Server serv)
    {

	if((flags & F_INIT) > 0)
	    return true;

	if(server == null && serv != null)
	    server = serv;
	else if(server == null)
	    server = new FileServer();

	//NO need for ARGNAME_TMA

	flags |= F_INIT;
	return true;
    }


    /**
     * <b>init_new_user</b> creates a new user with given details:
     * @param name 
     * 		id of the user
     *
     * @return pid
     *         puppy id for the user
     *
     * The method populates a <b>JSONObject</b> as follows:
     * {
     *	USR_ID: {name},
     *	USR_PWD: {pwd},
     *	USR_PUPPY_ID: <new puppy id>,
     *	USR_TRANSACTION_ID: NULL_ID,
     *	USR_EXTRAS: {},
     * }
     */

    public static JSONObject
    init_new_user(
	    String name,
	    String pwd
	    )
    {
	JSONObject user_rw = new JSONObject();
	return init_new_user(name, pwd, user_rw);
    }
    
    public static Integer
    get_new_pid()
    {
	// random id from 0 to INIT_MAX_PID
	return Integer.valueOf(Math.round(
		    Math.round(Math.random() * INIT_MAX_PID)
		    ));
    }

    public static JSONObject
    init_new_user(
	    String name,
	    String pwd,
	    JSONObject user_rw
	    )
    {

	user_rw.put(USR_ID, name);
	user_rw.put(USR_PWD, pwd);
	user_rw.put(USR_EXTRAS, new JSONObject());
	user_rw.put(USR_TRANSACTION_ID, NULL_ID);
	user_rw.put(USR_PUPPY_ID, get_new_pid());

	return user_rw;

    }

    public Object
    set_extras(String key, Object value)
    {
	if(!(this.user_rw.has(USR_EXTRAS)) || !( this.user_rw.get(USR_EXTRAS) instanceof JSONObject))
		this.user_rw.put(USR_EXTRAS, new JSONObject());

	return this.user_rw.getJSONObject(USR_EXTRAS).put(key, value);
    }

    public Boolean
    has_extras(String key)
    {

	if(!(this.user_rw.has(USR_EXTRAS)) || !( this.user_rw.get(USR_EXTRAS) instanceof JSONObject))
		this.user_rw.put(USR_EXTRAS, new JSONObject());
	return this.user_rw.getJSONObject(USR_EXTRAS).has(key);
    }

    public Object
    get_extras(String key)
    {
	if(!(this.user_rw.has(USR_EXTRAS)) || !( this.user_rw.get(USR_EXTRAS) instanceof JSONObject))
		this.user_rw.put(USR_EXTRAS, new JSONObject());
	if(this.user_rw.getJSONObject(USR_EXTRAS).has(key))
	    return this.user_rw.getJSONObject(USR_EXTRAS).get(key);

	return null;

    }

    protected static JSONObject
    load_user_rw(String name)
    {
	init(null);
	String data = server.get(name);
	JSONObject user_rw;
	
	try
	{
	    user_rw = (data != null)?
		new JSONObject(data) :
		new JSONObject();
	}catch(JSONException exp)
	{
	    user_rw = new JSONObject();
	}

	return user_rw;
    }

    private JSONObject
    load_user_rw()
    {
	return load_user_rw(this.name);
    }

    private JSONObject
    load_user_r(String name)
    {
	String data = this.server.get(name);
	JSONObject user_r;
	
	try
	{
	    user_r = (data != null)?
		new JSONObject(data) :
		new JSONObject();
	}catch(JSONException exp)
	{
	    user_r = new JSONObject();
	}

	if(!(user_r.has(USR_TRANSACTION_ID) && user_r.has(USR_SLOTS)))
	{
	    user_r.put(USR_TRANSACTION_ID, NULL_ID);
	    user_r.put(USR_SLOTS, NO_SLOT);
	}

	return user_r;
    }

    public boolean
    load_user_r()
    {
	this.user_r = load_user_r(this.name_r);

	return true;
    }


    public String
    revStr(String source)
    {

	char[] rev = source.toCharArray();

	for(int idx = rev.length, idx1 = 0;idx >= 0;)
	    rev[--idx] = source.charAt(idx1++);

	return new String(rev);

    }

    private String
    to_name_r(String name)
    {
	return name + ".rc";
    }

    private boolean
    is_user_rw_empty(JSONObject user_rw)
    {

	return !(
		user_rw.has(USR_ID) &&
		user_rw.has(USR_PWD) &&
		user_rw.has(USR_TRANSACTION_ID) &&
		user_rw.has(USR_PUPPY_ID)
		);
    }

    private Boolean
    write_puppy(List<String> cmdline, Namespace args, File filename)
    {
	return write_puppy(cmdline, args, filename.getName());
    }

    /**
     * Populates the <b>user_rw</b> data with command line.
     * {
     *	...
     *  USR_TRANSACTION: [
     *    ...
     *	  {
     *	     "name": {name},
     *	     "cmdline": {cmdline}
     *	  }
     *	  ...
     *  ],
     *  USR_TRANSACTION_ID: <new id>,
     *	...
     * }
     *
     * @param args
     * 		preprocessed command line
     * @param name
     * 		canonical name of the source of the command line
     *
     * @return Whether operation was successful or not.
     * 
     */

    private Boolean
    write_puppy(List<String> cmdline, Namespace args, String name)
    {
	JSONObject job = new JSONObject();

	job.put(USR_JOB_NAME, name);
	job.put(USR_JOB_CMDLINE, new JSONArray(cmdline));
	return put_job_queue(job, args);

    }

    private Boolean
    put_job_queue(JSONObject job, Namespace args)
    {
	if(getSlots() < MIN_SLOT)
	    return false;

	JSONArray queue;

	if(this.user_rw.getInt(USR_TRANSACTION_ID) > getTid())
	{
	    queue = this.user_rw.getJSONArray(USR_TRANSACTION);
	}else
	{
	    queue = new JSONArray();
	}

	queue.put(job);

	this.user_rw.put(USR_TRANSACTION, queue);

	Integer tid = this.user_rw.getInt(USR_TRANSACTION_ID);
	
	this.user_rw.put(USR_TRANSACTION_ID, ++tid);
	return true;

    }

    
    protected List<JSONObject>
    toDogProcessed(Collection<String> cmdline)
    {
	return toDogProcessed(cmdline.toArray(new String[cmdline.size()]));
    }

    protected List<JSONObject>
    toDogProcessed(String[] cmdline)
    {

	Namespace args = null;

	try
	{
	    args = parser.parseArgs(cmdline);

	}catch(ArgumentParserException argExp)
	{
	    return null;
	}

	List<Object> matno = args.get(arg_dest[ARGNAME_MATNO]);
	List<Object> pwd = args.get(arg_dest[ARGNAME_PWD]);
	List<Object> crscode = args.get(arg_dest[ARGNAME_CRSCODE]);

	Integer argc = Math.max(matno.size(), crscode.size());

	String mt, pw, cr;

	List<JSONObject> res = new List<JSONObject>(argc);
	Map<String, JSONObject> cache = new Map<String, JSONObject>();

	for(int idx = 0; idx < argc; idx++)
	{
	    if(idx < matno.size())
		mt = (String)matno.get(idx);

	    if(idx < pwd.size())
		pw = (String)pwd.get(idx);

	    if(idx < crscode.size())
		cr = (String)crscode.get(idx);

	    String[] crs = cr.split("\\s+");

	    for(String cc : crs)
	    {
		JSONObject info = new JSONObject();
	    }
	}
    }

    protected List<JSONObject>
    toDogProcessed(JSONArray cmdline)
    {
	return toDogProcessed(cmdline.toList());
    }

    public Integer
    getSlots()
    {
	load_user_r();
	return user_r.getInt(USR_SLOTS);
    }

    /**
     * <code>getTransactions</code> fetches user's readonly data and returns an array of all transactions, as <code>JSONObject</code>, that have been processed by a Dog - the keys are:
     * {
     * matno: <matno>,
     * pwd: <pwd>,
     * status: <OK, wrong credentials>,
     * cmdline: all css000 ...
     * crscodes:[ 
     * 		...
     *		{
     *		crs: <crscode>,
     *		status: <pending, submitted>,
     *		score : <int, unknown>,
     *		index: <1-3>
     *		}
     * 		...
     *		]
     *	}
     */

    public JSONArray
    getTransactions()
    {
	load_user_r();
	if(!(this.user_r.has(USR_TRANSACTION)))
	    return new JSONArray();

	JSONArray tlist = this.user_r.getJSONArray(USR_TRANSACTION);


	/**
	for(Iterable<JSONArray> it = tlist.iterator(); it.hasNext();)
	{
	    //fill missing details with defaults
	    JSONObject user = it.next();
	    if(user.has(USR_TRANSC_CRSCODES)
	}
	*/

	return tlist;
    }

    public JSONArray
    getPendingTransactions()
    {
	if(!(this.user_rw.getInt(USR_TRANSACTION_ID) > getTid()))
	    return new JSONArray();

	JSONArray tlist = this.user_r.getJSONArray(USR_TRANSACTION);
	return tlist;
    }

    Integer
    getTid()
    {
	load_user_r();
	return this.user_r.getInt(USR_TRANSACTION_ID);
    }


    public Object
    flush()
    {
	return server.put(this.name, user_rw.toString());
    }

    public static Boolean
    user_exists(String name, String pwd)
    {
	init(null);
	Boolean ne = server.exists(name);
	JSONObject udata = load_user_rw(name);
	return ne && udata.has(USR_PWD) && pwd.compareTo(udata.getString(USR_PWD)) == 0;

    }


    public static Boolean
    user_exists(String name)
    {
	init(null);
	return server.exists(name);

    }


    void logout() { this.user_rw.put(USR_PUPPY_ID, NULL_ID); };
    void close() {};
}
