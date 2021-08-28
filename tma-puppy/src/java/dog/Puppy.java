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
import java.util.Iterable;


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

    private static final String[][] all_args = {
	{"--matno"},
	{"--pwd"},
	{"--crscode"},
	{"--tma"}
    };

    private static final String arg_dest[] = {
	"matno",
	"pwd",
	"crscode",
    };

    private static final int
	ARGNAME_MATNO = 0,
	ARGNAME_PWD = 1,
	ARGNAME_CRSCODE = 2,
	ARGNAME_TMA = 3;


    private static byte flags = 0;
    
    private static final byte
	F_INIT = 0b0001;


    public static final String
	MSG_INVALID_PID = "User already logged-in another device",
	MSG_INVALID_NAME = "Invalid Username",
	MSG_INVALID_PWD = "Invalid password";
    
    private static final byte
	NULL_ID = 0,
	INIT_MAX_PID = 10,
	NO_SLOT = 0,
	MIN_SLOT = 1;

    public static final String
	USR_ID = "uid",
	USR_PWD = "pwd",
	USR_TRANSACTION_ID = "tid",
	USR_TRANSACTION = "tranc",
	USR_PUPPY_ID = "pid",
	USR_EXTRAS = "extras",
	USR_CRSCODES = "courses",
	USR_SLOTS = "slots",
	USR_TRANSC_MATNO = "matno",
	USR_TRANSC_PWD = "pwd",
	USR_TRANSC_STATUS = "status",
	USR_TRANSC_CRSCODES = "crscodes",
	USR_TRANSC_CRSCODES_CRS = "crs",
	USR_TRANSC_CRSCODES_STATUS = "status",
	USR_TRANSC_CRSCODES_SCORE = "score",
	USR_JOB_CMDLINE = "cmdline",
	USR_JOB_NAME = "name";
    


    private final JSONObject user_rw;

    private JSONObject user_r;

    public final String
	name,
	name_r,
	pwd;
    
    public final Server server;

    //Puppy id
    public final Integer pid;

    private static final ArgumentParser parser = ArgumentParsers.newFor(null).build();

    Puppy(
	    String name,
	    String pwd,
	    Integer pid
	 )
	throws AuthError
    {
	this(name, pwd, pid, null);
    }

    Puppy(
	    String name,
	    String pwd,
	    Integer pid,
	    Server server
	    )
	    throws AuthError
    {
	init();
	this.server = (server != null)? server : new FileServer();

	JSONObject user_rw = load_user_rw(name);

	if (is_user_rw_empty(user_rw))
	{
	    user_rw = init_new_user(name, pwd, user_rw);
	    pid = user_rw.getInt(USR_PUPPY_ID);

	} else
	{

	    if(name != user_rw.getString(USR_ID))
		throw new AuthError(
			MSG_INVALID_NAME + String.format(" %s", name));


	    if(pwd != user_rw.getString(USR_PWD))
		throw new AuthError(
			MSG_INVALID_PWD + String.format(" %s", pwd));

	    if(pid != user_rw.getInt(USR_PUPPY_ID))
		throw new AuthError(MSG_INVALID_PID);
	}

	this.name = name;
	this.pwd = pwd;
	this.pid = pid;

	this.user_rw = user_rw;
	
	this.name_r = to_name_r(name);

	this.user_r = load_user_r(this.name_r);


    }

    
    private static boolean
    init()
    {

	if((flags & F_INIT) > 0)
	    return true;

	parser.defaultHelp(false);
	parser.addArgument(all_args[ARGNAME_MATNO])
	    .nargs("+")
	    .required(true)
	    .dest(arg_dest[ARGNAME_MATNO]);

	parser.addArgument(all_args[ARGNAME_PWD])
	    .nargs("+")
	    .required(true)
	    .dest(arg_dest[ARGNAME_PWD]);

	parser.addArgument(all_args[ARGNAME_CRSCODE])
	    .nargs("+")
	    .dest(arg_dest[ARGNAME_CRSCODE]);

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

    private JSONObject
    init_new_user(
	    String name,
	    String pwd
	    )
    {
	JSONObject user_rw = new JSONObject();
	return init_new_user(name, pwd, user_rw);
    }

    private JSONObject
    init_new_user(
	    String name,
	    String pwd,
	    JSONObject user_rw
	    )
    {

	user_rw.put(USR_ID, Integer.parseInt(name));
	user_rw.put(USR_PWD, pwd);
	user_rw.put(USR_EXTRAS, new JSONObject());
	user_rw.put(USR_TRANSACTION_ID, NULL_ID);
	// random id from 0 to INIT_MAX_PID
	Integer pid =  Integer.valueOf(Math.round(
		    Math.round(Math.random() * INIT_MAX_PID)
		    ));
	user_rw.put(USR_PUPPY_ID, pid);

	return user_rw;

    }

    public Object
    set_extras(String key, Object value)
    {
	if(!(this.user_rw.has(USR_EXTRAS)) || !( this.user_rw.get(USR_EXTRAS) instanceof JSONObject))
		this.user_rw.put(USR_EXTRAS, new JSONObject());

	return this.user_rw.getJSONObject(USR_EXTRAS).put(key, value);
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

    private JSONObject
    load_user_rw(String name)
    {
	String data = this.server.get(name);
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

    /**
     * <code><b>is_valid_argument</b></code> is used to check if a flag is recognized by the given <code>psr</code>
     * 
     * <b>NOTE:</b> This does not work for all kinds of flags and even <code>psr</code>
     */
    private String
    is_valid_argument(String arg)
    {

	for(int idx = 0; idx < all_args.length; idx++)
	{
	    String[] arg_grp = all_args[idx];

	    for(int idx1 = 0; idx1 < arg_grp.length; idx1++)
	    {
		if(arg_grp[idx1].startsWith(arg))
		    return arg_dest[idx].substring(0); 
	    }
	}

	return null;
    }
    
    Object
    read_line_v(List<String> lines, String ff)
    {
	Vector<String> argv = preprocess(lines.toArray(new String[lines.size()]));

	try
	{
	    Namespace args = parser.parseArgs(argv.toArray(new String[argv.size()]));
	    return write_puppy(argv, args, ff);

	}catch(ArgumentParserException argExp){
	    return argExp;
	}
    }

    Object
    read_tmafile(String filename)
    {

	File ff = new File(filename);

	if(!(ff.exists() && ff.isFile() && ff.canRead()))
		return Boolean.FALSE;


	try
	{
	    List<String> lines = Files.readAllLines(ff.toPath(), StandardCharsets.UTF_8);

	    return read_line_v(lines, ff.getName());
	}catch(IOException e)
	{
	    return null;
	}

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
     *  USR_TRANSACTION_ID: [
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
	    return Boolean.FALSE;

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
	return Boolean.TRUE;

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
     * status: <OK, wrong credentials>
     * crscodes:[ 
     * 		...
     *		{
     *		crs: <crscode>,
     *		status: <pending, submitted>,
     *		score : <int, unknown>,
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

    private Vector<String>
    preprocess(String[] arglines)
    {
	Vector<String> argv = new Vector<String>();
	
	String word;
	String[] argbuff = {"", "", ""};
	
	byte BUF_ARG_DEST = 0,
	     BUF_ARG_NAME = 1,
	     BUF_ARG_VAL = 2;

	/**
	 * <code>PFLAGS</code> holds states of the preprocessor.
	 * SWITCH_* are &'ed with this flag to set/reset states 
	 */
	byte PFLAGS = 0,
	     // mutually exlusives
	     SWITCH_ONE = 0b001,
	     SWITCH_MULTI = 0b010;
	
	PFLAGS = SWITCH_ONE;

	int lastbuf_id = 0, buf_id = 0;

	boolean in_switch = false;

	int lcount = arglines.length;

	for(int lidx = 0; lidx < lcount; lidx++)
	{
	    if(arglines[lidx].isEmpty())
		continue;

	    String[] line = arglines[lidx].split("\\s");
	    for(int widx = 0; widx < line.length; widx++)
	    {
		word = line[widx];
		word = (word.isEmpty())? " " : word;
		String wchk = is_valid_argument(word);
		if(wchk != null)
		{
		    if(wchk == arg_dest[ARGNAME_MATNO])
			PFLAGS = SWITCH_ONE;

		    else
			PFLAGS = SWITCH_MULTI;

		    if(buf_id > lastbuf_id && argbuff[BUF_ARG_VAL] != null)
		    {
			argv.add(argbuff[BUF_ARG_NAME]);
			argv.add(argbuff[BUF_ARG_VAL].trim());
			lastbuf_id = buf_id;
		    }
		    
		    //argbuff[BUF_ARG_DEST] = wchk;
		    argbuff[BUF_ARG_NAME] = word;
		    argbuff[BUF_ARG_VAL] = null;
		    buf_id++;

		}else if(PFLAGS == SWITCH_ONE)
		{
		    if(word.isBlank())
			continue;
		    
		    argv.add(all_args[ARGNAME_MATNO][0]);
		    argv.add(word);
		    lastbuf_id = buf_id;

		    /**
		     * passwords should be sought by default unless prompted otherwise by a non-password flag.
		     */
		    PFLAGS = SWITCH_MULTI;
		    //argbuff[BUF_ARG_DEST] = arg_dest[ARGNAME_PWD];
		    argbuff[BUF_ARG_NAME] = all_args[ARGNAME_PWD][0];
		    argbuff[BUF_ARG_VAL] = null;
		    buf_id++;

		}else if(!(word.isBlank()) &&
			widx == 0 && buf_id >
			lastbuf_id &&
			argbuff[BUF_ARG_VAL] !=
			null)
		{
		    argv.add(argbuff[BUF_ARG_NAME]);
		    argv.add(argbuff[BUF_ARG_VAL].trim());
		    lastbuf_id = buf_id;

		    argv.add(all_args[ARGNAME_MATNO][0]);
		    argv.add(word.trim());
		    PFLAGS = SWITCH_MULTI;
		    //argbuff[BUF_ARG_DEST] = P_PWD;
		    argbuff[BUF_ARG_NAME] = all_args[ARGNAME_PWD][0];
		    argbuff[BUF_ARG_VAL] = null;
		    buf_id++;

		}else
		{
		    if(argbuff[BUF_ARG_VAL] == null)
			argbuff[BUF_ARG_VAL] = word;
		    else
			argbuff[BUF_ARG_VAL] += " " + word;
		}




	    }
	}

	if(buf_id > lastbuf_id && argbuff[BUF_ARG_VAL] != null)
	{
	    argv.add(argbuff[BUF_ARG_NAME]);
	    argv.add(argbuff[BUF_ARG_VAL].trim());
	}

	return argv;
    }

    void logout() {};
    void close() {};
}
