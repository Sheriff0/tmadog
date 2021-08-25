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
import java.awt.List;
import java.util.ArrayList;
import java.nio.file.Path;
import java.nio.file.FileSystems;
import java.nio.file.Files;
import java.io.IOException;
import java.util.Set;
import java.io.File;


import net.sourceforge.argparse4j.ArgumentParsers;
import net.sourceforge.argparse4j.inf.ArgumentParser;
import net.sourceforge.argparse4j.inf.Namespace;

import net.sourceforge.argparse4j.internal.UnrecognizedArgumentException;
import net.sourceforge.argparse4j.inf.ArgumentParserException;

import org.json.JSONObject;

class 
Puppy
{

    private final String[][] all_args = {
	{"--matno"},
	{"--pwd"},
	{"--crscode"},
	{"--tma"}
    };

    private final String arg_dest[] = {
	"matno",
	"pwd",
	"crscode",
    };

    private final int
	ARGNAME_MATNO = 0,
	ARGNAME_PWD = 1,
	ARGNAME_CRSCODE = 2,
	ARGNAME_TMA = 3;


    private byte flags = 0;
    
    private static final byte
	F_INIT = 0b0001;


    public static final byte
	MSG_INVALID_PID = 0,
	MSG_INVALID_NAME = 1,
	MSG_INVALID_PWD = 2;
    
    public static final byte
	NULL_ID = 0,
	INIT_MAX_PID = 10;

    public static final String
	USR_ID = "uid",
	USR_PWD = "pwd",
	USR_TRANSACTION_ID = "tid",
	USR_TRANSACTION = "tranc",
	USR_PUPPY_ID = "pid",
	USR_EXTRAS = "extras",
	// for reads
	USR_CRSCODES = "courses",

	USR_JOB_CMDLINE = "cmdline",
	USR_JOB_NAME = "name";

    private Server server;

    private JSONObject
	user_rw,
	user_r;

    private String
	name,
	name_r,
	pwd;
    
    //Puppy id
    private Integer pid;

    private final ArgumentParser parser = ArgumentParsers.newFor(null).build();

    Puppy(
	    String name,
	    String pwd,
	    Integer pid,
	 )
    {
	this(name, pwd, pid, null, null);
    }

    Puppy(
	    String name,
	    String pwd,
	    Integer pid,
	    Server server,
	    JSONObject initials
	    ) throws AuthError
    {
	user_rw = load_user_rw(name);

	if (is_user_rw_empty(user_rw))
	{
	    user_rw = init_new_user(name, pwd, user_rw);
	    pid = user_rw.get(USR_PUPPY_ID);

	} else
	{

	    if(name != user_rw.get(USR_ID).toString())
		throw new AuthError(MSG_INVALID_NAME);


	    if(pwd != user_rw.get(USR_PWD))
		throw new AuthError(MSG_INVALID_PWD);

	    if(pid != user_rw.getInt(USR_PUPPY_ID))
		throw new AuthError(MSG_INVALID_PID);
	}

	this.name = name;
	this.pwd = pwd;
	this.pid = pid;

	this.user_rw = user_rw;
	
	this.name_r = to_user_r(name);

	this.user_r = load_user_r(this.name_r);

	this.server = (server != null)? server : new FileServer();

	//Check if we have initial data,
	//e.g from a previous unsuccessful attempt to flush to server.
	
	update_from_obj(initials);
    }

    
    public JSONType set_extras(String key, Object value);
    public JSONType get_extras(String key);


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
	    String pwd,
	    )
    {
	JSONObject user_rw = new JSONObject();
	return init_new_user(name, pwd, user_rw);
    }

    private JSONObject
    init_new_user(
	    String name,
	    String pwd,
	    JSONObject user_rw,
	    )
    {

	user_rw.set(USR_ID, Integer.parseInt(name));
	user_rw.set(USR_PWD, pwd);
	user_rw.set(USR_EXTRAS, new JSONObject());
	user_rw.set(USR_TRANSACTION_ID, NULL_ID);
	// random id from 0 to INIT_MAX_PID
	Integer pid =  Integer.valueOf(Math.round(Math.random() * INIT_MAX_PID));
	user_rw.set(USR_PUPPY_ID, pid);

	return user_rw;

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

    private boolean
    load_user_rw()
    {
	return load_user_rw(this._name);
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

	if(;
    }

    private boolean
    load_user_r()
    {
	this.user_r = load_user_r(this.name_r);

	return true;
    }


    private String
    to_user_r(String name)
    {

	char[] rev = name.toCharArray();

	int idx = rev.length - 1, idx1 = 0;

	for(;idx >= 0; idx1++)
	    rev[idx--] = name.charAt(idx1);

	return new String(rev);

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
	init();

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
    
    void
    read_line_v(ArrayList<String> arglines)
    {

    }

    Object
    read_tmafile(String filename)
    {

	File ff = new File(filename);

	if(!(ff.exists() || !(ff.isFile()) || !(ff.canRead()))
		return false;


	List lines = Files.readAllLines(ff.toPath(), StandardCharsets.UTF_8);

	Vector<String> argv = preprocess(new String[lines.size()]);

	try
	{
	    Namespace args = parser.parseArgs(argv.toArray(new String[argv.size()]));
	    return write_puppy(argv, args, ff.getName());

	}catch(ArgumentParserException argExp){
	    return argExp;
	}
    }

    private Boolean
    write_puppy(String[] cmdline, Namespace args, File filename)
    {
	return write_puppy(cmdline, args, filename.getName());
    }

    /**
     * Populates the <b>_user_rw</b> data with command line.
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
    write_puppy(Vector<String> cmdline, Namespace args, String name)
    {
	JSONObject job = new JSONObject();

	job.put(USR_JOB_NAME, name);
	job.put(USR_JOB_CMDLINE, cmdline);
	return put_rw_queue(job, args);

    }

    private boolean
    put_rw_queue(JSONObject job, args)
    {
	if(get_r_Int(USR_SLOTS) < 1)
	    return false;

	JSONArray queue;

	if(get_rw_Int(USR_TRANSACTION_ID) > get_r_Int(USR_TRANSACTION_ID))
	{
	    queue = get_rw_JSONArray(USR_TRANSACTION);
	}else
	{
	    queue = new JSONArray();
	}

	queue.put(job);

	put_rw(USR_TRANSACTION, queue);

	Integer tid = get_rw_Int(USR_TRANSACTION_ID);
	return put_rw(USR_TRANSACTION_ID, ++tid);

    }
    
    public JSONArray
    get_rw_JSONArray(String key)
    {
	return this.user_rw.getJSONArray(key);
    }

    public Integer
    get_rw_Int(String key)
    {
	return this.user_rw.getInt(key);
    }

    public Object
    get_rw(String key)
    {
	return this.user_rw.get(key);
    }

    private boolean
    put_rw(String key, Object value)
    {
	this.user_rw.put(key, value);
    }

    private Boolean
    write_puppy(Namespace args, String name){};

    public Object
    flush()
    {
	return server.post(this._name, _user_rw.toString());
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

    void
    update_from_args()
    {

    }

    void logout() {};
    void close() {};
}
