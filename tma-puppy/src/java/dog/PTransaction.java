package dog;
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
import java.lang.Collection;
import java.util.Map;
import java.util.Iterator;


import net.sourceforge.argparse4j.ArgumentParsers;
import net.sourceforge.argparse4j.inf.ArgumentParser;
import net.sourceforge.argparse4j.inf.Namespace;

import net.sourceforge.argparse4j.internal.UnrecognizedArgumentException;
import net.sourceforge.argparse4j.inf.ArgumentParserException;

import org.json.JSONObject;
import org.json.JSONArray;
import org.json.JSONException;


public class
PTransaction
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

    static private String
	SCORES = "scores",
	CNAME = "cname";


    private static final ArgumentParser parser = init_parser();

    private static ArgumentParser
    init_parser()
    {
	ArgumentParser parser = ArgumentParsers.newFor(null).addHelp(false).build();

	parser.addArgument(all_args[ARGNAME_MATNO])
	    .nargs("+")
	    .required(true)
	    .action(new PAppendAction())
	    .dest(arg_dest[ARGNAME_MATNO]);

	parser.addArgument(all_args[ARGNAME_PWD])
	    .nargs("+")
	    .required(true)
	    .action(new PAppendAction())
	    .dest(arg_dest[ARGNAME_PWD]);

	parser.addArgument(all_args[ARGNAME_CRSCODE])
	    .nargs("+")
	    .action(new PAppendAction())
	    .dest(arg_dest[ARGNAME_CRSCODE]);

	return parser;
    }


    private Namespace args;


    Transaction(File tfile)
	throws IOException
    {
	this(read_tr(tfile));
	
    }

    Transaction(String tstr)
    {
	this(read_tr(tstr));
    }

    Transaction(Collection<String> argv)
    {

	ArgumentParser psr = ArgumentParsers.newFor(null).addHelp(false).build();

	psr.addArgument("--" + SCORES)
	    .dest(SCORES)
	    .nargs("+")
	    .action(new PAppendAction());

	psr.addArgument("--" + CNAME)
	    .dest(CNAME)
	    .nargs("+")
	    .action(new PAppendAction());

	List<String> rest = new List<String();

	Namespace args = parser.parseKnownArgs(argv.toArray(new String[argv.size()]), rest);

	args.getAttrs()
	    .putAll(
		    psr.parseKnownArgs(rest, null).getAttrs()
		    );

	this.args = args;

    }


    List<String>
    get_crscodes(Integer midx)
    {
	// check if courses are available in the given index
	List<String> crs = this.args.getList(arg_dest[ARGNAME_CRSCODE]);
	
	if(crs == null)
	    return null;

	int ccount = crs.size();

	if(midx >= ccount)
	    return null;
	
	crs = array_to_list<String>(crs.get(midx).split("\\s+"));
	
	return crs;
    }


    List<String>
    get_scores(Integer midx)
    {
	// check if courses are available in the given index
	List<String> crs = this.args.getList(arg_dest[ARGNAME_CRSCODE]);
	
	if(crs == null)
	    return null;

	int ccount = crs.size();

	if(midx >= ccount)
	    return null;
	
	// check if score is available
	List<String> scr = this.args.getList(SCORES);
	if(scr == null)
	    return null;

	int scount = scr.size();

	if(midx >= scount)
	    return null;

	scr = array_to_list<String>(scr.get(midx).split("\\s+"));
	scount = scr.size();

	crs = array_to_list<String>(crs.get(midx).split("\\s+"));
	ccount = crs.size();
	
	if(scount < ccount)
	{
	    for(int idx = 0; idx < ccount; idx++)
	    {
		if(idx >= scount)
		    scr.add("Unknown");

	    }
	}

	return scr.subList(0, ccount);
    }

    Integer
    matno_index(Object matno)
    {
	List<Object> mts = this.args.getList(arg_dest[ARGNAME_MATNO]);
	
	if(mts == null)
	    return -1;

	int mcount = mts.size();

	for(int idx = 0; idx < mcount; idx++)
	{
	    if(mts.get(idx).toString().compareToIgnoreCase(matno.toString())
		    == 0)
		return idx;
	}

	return -1;
    }

    Object
    get_pwd(Integer pidx)
    {

	List<Object> pwds = this.args.getList(arg_dest[ARGNAME_PWD]);
	
	if(pwds == null)
	    return null;

	int pcount = pwds.size();

	if(pidx >= pcount)
	    return null;

	return pwds.get(pidx);
    }

    List<Object>
    get_matnos()
    {
	List<Object> mts = this.args.getList(arg_dest[ARGNAME_MATNO]);
	
	if(mts == null)
	    return null;

	// minalimalist to protect consistency of
	// internal structures.
	return mts.clone();
    }

    JSONArray
    toJSON()
    {
	List<Object> argv = ArrayList<Object>();

	argv.add(all_args[ARGNAME_MATNO][0]);

	argv.addAll(this.args.getList(arg_dest[ARGNAME_MATNO]));

	argv.add(all_args[ARGNAME_PWD][0]);

	argv.addAll(this.args.getList(arg_dest[ARGNAME_PWD]));

	argv.add(all_args[ARGNAME_CRSCODE][0]);

	argv.addAll(this.args.getList(arg_dest[ARGNAME_CRSCODE]));

	return JSONArray(argv);
    }

    static public <T> List<T>
    array_to_list(T[] array)
    {
	ArrayList<T> list = new ArrayList<T>(array.length);

	for(T el : array)
	    list.add(el);

	return list;

    }


    List<String>
    read_tr(String str)
    {
	List<String> lines = array_to_list<String>(str.split("\n"));
	return preprocess(lines.toArray(new String[lines.size()]));
    }

    List<String>
    read_tr(File ff)
	throws IOException
    {

	if(!(ff.exists() && ff.isFile() && ff.canRead()))
	    return null;


	List<String> lines = Files.readAllLines(ff.toPath(), StandardCharsets.UTF_8);

	return preprocess(lines.toArray(new String[lines.size()]));

    }

    private List<String>
    preprocess(String[] arglines)
    {
	List<String> argv = new List<String>();
	
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
    
    String
    get_cmdline()
    {

    }

    String
    toJSON()
    {

    }
}

