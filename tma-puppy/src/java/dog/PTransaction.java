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
import java.util.Collection;
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
    protected static final String[][] all_args = {
	{"--matno"},
	{"--pwd"},
	{"--crscode"},
	{"--tma"}
    };

    protected static final String arg_dest[] = {
	"matno",
	"pwd",
	"crscode",
    };

    protected static final int
	ARGNAME_MATNO = 0,
	ARGNAME_PWD = 1,
	ARGNAME_CRSCODE = 2,
	ARGNAME_TMA = 3;

    static protected String
	SCORES = "scores",
	CNAME = "cname";


    private static final ArgumentParser parser = init_parser();

    protected ArrayList<Namespace> args_list;

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




    PTransaction(File tfile)
	throws IOException, ArgumentParserException
    {
	this(read_tr(tfile), tfile.getName());
	
    }

    PTransaction(String tstr)
	    throws ArgumentParserException
    {
	this((List<Object>)read_tr(tstr), null);
    }

    PTransaction(Collection<Object> argv)
	    throws ArgumentParserException
    {
	this((Collection<Object>[]) new Object[] {argv}, null);
    }

    PTransaction(Collection<Object> argv, String cname)
	    throws ArgumentParserException
    {
	this((Collection<Object>[]) new Object[] {argv}, cname);
    }

    PTransaction(Collection<Object>[] argv_list,
	    String cname)
	    throws ArgumentParserException
    {

	ArgumentParser psr = ArgumentParsers.newFor(null).addHelp(false).build();

	psr.addArgument("--" + SCORES)
	    .dest(SCORES)
	    .nargs("+")
	    .action(new PAppendAction());

	psr.addArgument("--" + CNAME)
	    .dest(CNAME)
	    .action(new PAppendAction());
	
	int llen = argv_list.length;

	ArrayList<Namespace> args_list = new ArrayList<Namespace>(llen);


	for(int idx = 0; idx < llen; idx++){ 
	    Collection<Object> argv = argv_list[idx];
	    ArrayList<String> rest = new ArrayList<String>();

	    // use custom 'psr' first to propagate errors from the main 'parser'
	    Namespace args = psr.parseKnownArgs(argv.toArray(new String[argv.size()]), (List<String>)rest);

	    args.getAttrs().putAll(
		    parser.parseArgs(rest.toArray(new String[rest.size()])).getAttrs()
		    );

	    if(cname != null)
		args.getAttrs().put(CNAME, cname);

	    args_list.add(args);
	}

	this.args_list = args_list;

    }

    Integer
    from2D(Integer[] dim2)
    {

	if(dim2 == null)
	    return null;

	return from2D(dim2[0], dim2[1]); 
    }

    Integer
    from2D(Integer d1, Integer d2)
    {

	int asize = this.args_list.size(),
	    midx = 0;

	for(int d0 = 0; d0 < asize; d0++)
	{
	    Namespace args = this.args_list.get(d0);
	    List<String> mts = args.getList(arg_dest[ARGNAME_MATNO]);

	    // args with no matnos are skipped and
	    // not considered in indexing.

	    if(mts == null)
		continue;

	    int msize = mts.size();

	    if(msize == 0)
		continue;

	    if(d0 == d1)
	    {
		midx += d2;
		return midx;
	    }

	    else
		midx += msize;

	}

	return null;
    }

    Integer[]
    to2D(Integer idx)
    {
	int asize = this.args_list.size(), d2 = idx;

	for(int d1 = 0; d1 < asize; d1++)
	{
	    Namespace args = this.args_list.get(d1);
	    List<String> mts = args.getList(arg_dest[ARGNAME_MATNO]);

	    // args with no matnos are skipped and
	    // not considered in indexing.

	    if(mts == null)
		continue;

	    int msize = mts.size();

	    d2 -= msize;

	    if(d2 >= 0)
		continue;

	    else
		d2 += msize;

	    return new Integer[] {d1, d2};
	}

	return null;
    }

    List<String>
    get_crscodes(Integer midx)
    {
	return get_crscodes(to2D(midx));
    }

    List<String>
    get_crscodes(Integer[] dim2)
    {
	if(dim2 == null)
	    return null;

	return get_crscodes(dim2[0], dim2[1]);
    }

    List<String>
    get_crscodes(Integer d1, Integer d2)
    {
	// check if courses are available in the given index
	
	Namespace args = this.args_list.get(d1);

	List<String> crs = args.getList(arg_dest[ARGNAME_CRSCODE]);

	// if true, something is wrong
	if(crs == null)
	    return null;

	int ccount = crs.size();

	if(d2 >= ccount)
	    return null;

	crs = array_to_list(crs.get(d2).split("\\s+"));

	return crs;

    }

    List<String>
    get_scores(Integer midx)
    {
	return get_scores(to2D(midx));
    }

    List<String>
    get_scores(Integer[] dim2)
    {
	if(dim2 == null)
	    return null;

	return get_scores(dim2[0], dim2[1]);
    }

    List<String>
    get_scores(Integer d1, Integer d2)
    {
	// check if courses are available in the given index
	Namespace args = this.args_list.get(d1);

	List<String> crs = get_crscodes(d1, d2);

	if(crs == null)
	    return null;

	int ccount = crs.size();

	// check if score is available
	List<String> scr = args.getList(SCORES);

	if(scr == null)
	    return null;

	int scount = scr.size();

	if(d2 >= scount)
	    return null;

	scr = array_to_list(scr.get(d2).split("\\s+"));
	scount = scr.size();

	// create a semblance of ccount == scount
	// fill with 'unknown'
	for(int idx = scount; idx < ccount; idx++)
	{
	    scr.add("Unknown");

	}

	return scr.subList(0, ccount);

    }

    //Integer
    //matno_index(Object matno, Integer from_idx)
    //{
    //    Integer[] dim2 = matno_index(matno, from_idx);
    //    if(dim2 == null)
    //        return null;

    //    return from2D(dim2);

    //}

    //Integer matno_index(Object matno) { return matno_index(matno, 0); };

    Integer[] matno_index(Object matno) { return matno_index(matno, 0, 0); };

    Integer[] matno_index(Object matno, Integer from_idx) { return matno_index(matno, to2D(from_idx)); };

    Integer[]
    matno_index(Object matno, Integer[] from_2d)
    {
	if(from_2d == null)
	    return null;

	return matno_index(matno, from_2d[0], from_2d[1]);
    }

    Integer[]
    matno_index(Object matno, Integer from_d1, Integer from_d2)
    {

	int asize = this.args_list.size();

	for(int d1 = from_d1; d1 < asize; d1++)
	{
	    Namespace args = this.args_list.get(d1);

	    List<String> mts = args.getList(arg_dest[ARGNAME_MATNO]);


	    int mcount = mts.size();

	    // out of bound
	    if(from_d2 >= mcount)
		return null;

	    for(int d2 = from_d2; d2 < mcount; d2++)
	    {
		if(mts.get(d2).compareToIgnoreCase(matno.toString())
			== 0)
		    return new Integer[] {d1, d2};
	    }

	    //reset
	    from_d2 = 0;

	}

	return null;
    }

    Object get_pwd(Integer pidx) throws ConsistencyError { return get_pwd(to2D(pidx)); };

    Object
    get_pwd(Integer dim2[])
	throws ConsistencyError
    {
	if(dim2 == null)
	    return null;

	return get_pwd(dim2[0], dim2[1]);
    }

    Object
    get_pwd(Integer d1, Integer d2)
	throws ConsistencyError
    {

	int asize = this.args_list.size();

	Namespace args = this.args_list.get(d1);

	Object mt = get_matno(d1, d2);

	if(mt == null)
	    return null;

	List<String> pwds = args.getList(arg_dest[ARGNAME_PWD]);

	// must be equal or less or something is wrong
	if(pwds == null || d2 >= pwds.size())
	    throw new ConsistencyError(
		    "password error: matno == mcount"
		    );

	return pwds.get(d2);

    }

    Object get_matno(Integer midx) { return get_matno(to2D(midx)); };

    Object
    get_matno(Integer[] dim2)
    {
	if(dim2 == null)
	    return null;

	return get_matno(dim2[0], dim2[1]);
    }

    Object
    get_matno(Integer d1, Integer d2)
    {

	int asize = this.args_list.size();

	Namespace args = this.args_list.get(d1);

	List<String> mts = args.getList(arg_dest[ARGNAME_MATNO]);

	if(mts == null)
	    return null;

	int mcount = mts.size();

	if(d2 >= mcount)
	    return null;

	return mts.get(d2);

    }


    PIterator iterator() { return new PIterator(this); };

    PIterator iterator(Integer from_idx) { return new PIterator(this, from_idx); };

    List<List<String>>
    tr2list()
    {
	
	int asize = this.args_list.size();

	List<List<String>> all_argv = new ArrayList<List<String>>(asize);

	for(int d1 = 0; d1 < asize; d1++)
	{
	    Namespace args = this.args_list.get(d1);
	    List<String> argv = new ArrayList<String>();

	    if(args.getAttrs().containsKey(CNAME) && args.get(CNAME) != null)
	    {
		argv.add("--" + CNAME);
		argv.add(args.get(CNAME));
	    }

	    argv.add(all_args[ARGNAME_MATNO][0]);

	    argv.addAll(args.getList(arg_dest[ARGNAME_MATNO]));

	    argv.add(all_args[ARGNAME_PWD][0]);

	    argv.addAll(args.getList(arg_dest[ARGNAME_PWD]));

	    argv.add(all_args[ARGNAME_CRSCODE][0]);

	    argv.addAll(args.getList(arg_dest[ARGNAME_CRSCODE]));

	    all_argv.add(argv);

	}

	return all_argv;
    }

    public static <T> List<T>
    array_to_list(T[] array)
    {
	ArrayList<T> list = new ArrayList<T>(array.length);

	for(T el : array)
	    list.add(el);

	return list;

    }

    public static <T1> ArrayList<T1>
    as_list(T1 ele)
    {
	ArrayList<T1> arr = new ArrayList<T1>();
	arr.add(ele);
	return arr;
    }


    private static List<Object>
    read_tr(String str)
    {
	List<String> lines = array_to_list(str.split("\n"));
	return preprocess(lines.toArray(new String[lines.size()]));
    }

    private static List<Object>
    read_tr(File ff)
	throws IOException
    {

	if(!(ff.exists() && ff.isFile() && ff.canRead()))
	    return null;


	List<String> lines = Files.readAllLines(ff.toPath(), StandardCharsets.UTF_8);

	return preprocess(lines.toArray(new String[lines.size()]));

    }

    private static List<Object>
    preprocess(String[] arglines)
    {
	List<Object> argv = new ArrayList<Object>();
	
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
    private static String
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

    public static class
    PIterator
    {
	private final PTransaction tr;

	Integer index;

	Integer[] dim2;

	PIterator(PTransaction tr, Integer from_idx)
	{
	    this.tr = tr;
	    this.index = from_idx;
	    this.dim2 = this.tr.to2D(this.index);
	}

	PIterator(PTransaction tr)
	{
	    this(tr, 0);
	}

	boolean
	hasNext()
	{
	    // you need another iterator if the underlying transaction size changes
	    if(this.dim2 == null)
		return false;

	    this.dim2 = this.tr.to2D(++this.index);

	    return this.dim2 != null;
	}

	Object getNext_matno() { return this.tr.get_matno(this.dim2); };

	Object
	getNext_pwd()
	{
	    try
	    {
		return this.tr.get_pwd(this.dim2);

	    }catch(PTransaction.ConsistencyError e)
	    {
		return null;
	    }
	}

	Object getNext_crscodes() { return this.tr.get_crscodes(this.dim2); };

	Object getNext_scores() { return this.tr.get_scores(this.dim2); };
    }

    public static class
    ConsistencyError extends RuntimeException
    {
	/** Serialization ID */
	private static final long serialVersionUID = 0;

	/**
	 *
	 * @param message
	 *            Detail about the reason for the exception.
	 */
	public ConsistencyError(final String message) {
	    super(message);
	}

	/**
	 * 
	 * @param message
	 *            Detail about the reason for the exception.
	 * @param cause
	 *            The cause.
	 */
	public ConsistencyError(final String message, final Throwable cause) {
	    super(message, cause);
	}

	/**
	 * 
	 * @param cause
	 *            The cause.
	 */
	public ConsistencyError(final Throwable cause) {
	    super(cause.getMessage(), cause);
	}

    }

}
