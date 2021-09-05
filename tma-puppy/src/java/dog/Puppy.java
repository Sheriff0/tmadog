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
import java.util.Collection;

import net.sourceforge.argparse4j.ArgumentParsers;
import net.sourceforge.argparse4j.inf.ArgumentParser;
import net.sourceforge.argparse4j.inf.Namespace;

import net.sourceforge.argparse4j.internal.UnrecognizedArgumentException;
import net.sourceforge.argparse4j.inf.ArgumentParserException;

import org.json.JSONObject;
import org.json.JSONArray;
import org.json.JSONException;

public class 
Puppy
{
    private static byte flags = 0;
    
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
	USR_SLOTS = "slots";



    private final JSONObject user_rw;

    private JSONObject user_r;

    public final String
	name,
	name_r,
	pwd;
    
    protected final Server server;

    //Puppy id
    public final Integer pid;

    Puppy(
	    String name,
	    String pwd,
	    Integer pid,
	    Server server
	    )
	    throws AuthError
    {

	JSONObject user_rw = load_user_rw(name, server);

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

	assert server != null: "Server must not be null";
	this.user_r = load_user_r(this.name_r, server);
	this.server = server;

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
    load_user_rw(String name, Server server)
    {
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
	return load_user_rw(this.name, this.server);
    }

    protected static JSONObject
    load_user_r(String name, Server server)
    {
	String data = server.get(name);
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
	this.user_r = load_user_r(this.name_r, this.server);

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

    //public Boolean
    //write_tr(Collection<Object> argv)
    //    throws ArgumentParserException
    //{
    //    return put_job_queue(new PTransaction(argv));
    //}

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

    public Boolean
    write_tr(File tr_file)
	throws IOException, ArgumentParserException
    {

	return put_job_queue(new PTransaction(tr_file));

    }

    private Boolean
    stingy_put_queue(PTransaction job)
    {
	//implement
	
	// always
	return false;
    }

    private Boolean
    put_job_queue(PTransaction job)
    {
	if(getSlots() < MIN_SLOT)
	    return stingy_put_queue(job);

	JSONArray queue;

	if(this.user_rw.getInt(USR_TRANSACTION_ID) > getTid() && this.user_rw.has(USR_TRANSACTION))
	{
	    queue = this.user_rw.getJSONArray(USR_TRANSACTION);
	}else
	{
	    queue = new JSONArray();
	}

	var ll = job.tr2list();
	
	if(ll == null || ll.size() == 0)
	    return false;

	queue.putAll(ll);

	this.user_rw.put(USR_TRANSACTION, queue);

	Integer tid = this.user_rw.getInt(USR_TRANSACTION_ID);
	
	this.user_rw.put(USR_TRANSACTION_ID, ++tid);
	return true;

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

    public PTransaction
    getTransactions()
    {
	load_user_r();
	if(!(this.user_r.has(USR_TRANSACTION)))
	    return null;

	try
	{
	    var ll = this.user_r.getJSONArray(USR_TRANSACTION).toList();

	 return new PTransaction(tr_fy(ll));

	}catch(ArgumentParserException argExp){
	    return null;
	}
    }

    private <T> List<List<T>>
    tr_fy(List<?> ll)
    {
	int llen = ll.size();

	ArrayList<ArrayList<T>> tr_fied = new ArrayList<ArrayList<T>>(llen);
	
	for(int idx = 0; idx < llen; idx++)
	{
	    tr_fied.add((ArrayList<T>)ll.get(idx));
	}

	return (List)tr_fied;
    }

    public PTransaction
    getPendingTransactions()
    {
	if(!(this.user_rw.getInt(USR_TRANSACTION_ID) > getTid()))
	    return null;

	if(!(this.user_rw.has(USR_TRANSACTION)))
		return null;
	try
	{
	    var ll = this.user_rw.getJSONArray(USR_TRANSACTION).toList();
	 return new PTransaction(tr_fy(ll));

	} catch (ArgumentParserException e)
	{
	    return null;
	}
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
	return this.server.put(this.name, user_rw.toString());
    }


    void logout() { this.user_rw.put(USR_PUPPY_ID, NULL_ID); };
    void close() {};
}
