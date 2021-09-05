import java.io.InputStreamReader;
import java.io.BufferedReader;
import java.nio.file.Files;
import java.io.File;
import java.nio.file.FileSystems;
import java.util.List;
import java.util.ArrayList;
import java.io.IOException;


import dog.Puppy;
import dog.FPuppy;
import dog.AuthError;

import org.json.JSONObject;

import net.sourceforge.argparse4j.ArgumentParsers;
import net.sourceforge.argparse4j.inf.ArgumentParser;
import net.sourceforge.argparse4j.inf.Namespace;

import net.sourceforge.argparse4j.internal.UnrecognizedArgumentException;
import net.sourceforge.argparse4j.inf.ArgumentParserException;
import net.sourceforge.argparse4j.impl.action.StoreConstArgumentAction;
import net.sourceforge.argparse4j.impl.action.StoreTrueArgumentAction;


public class
IPuppy
{
    public static void
    pending(String[] argv, Puppy puppy, JSONObject user, BufferedReader stdin)
    {

	Integer def = 5;

	ArgumentParser parser = ArgumentParsers.newFor("").addHelp(false).build();

	parser.addArgument("lines")
	    .type(def.getClass()).setDefault(def);

	    Namespace args = null;
	try{
	    args = parser.parseArgs(argv);

	}catch(ArgumentParserException argExp){
	    parser.printUsage();
	    return;
	}
	
	var t = puppy.getPendingTransactions();
	
	if(t == null)
	{
	    System.out.println("None");
	    return;
	}
    
	var tr = t.iterator();

	int len = args.getInt("lines");

	for(int l = args.getInt("lines"); l > 0 && tr.hasNext(); --l)
	{
	    System.out.printf("(%d)\n\tMatric No: %s\n\tPassword: %s\n\tCourses: %s\n\tScores: %s\n", (len - l) + 1, tr.getNext_matno(), tr.getNext_pwd(), tr.getNext_crscodes(), tr.getNext_scores());
	}
    }

    public static void
    tfile(String[] argv, Puppy puppy, JSONObject user, BufferedReader stdin)
    {

	ArgumentParser parser = ArgumentParsers.newFor("tfile").addHelp(false).build();

	parser.addArgument("filename")
	    .help("file containing your matrics and password");

	    Namespace args = null;
	try{
	    args = parser.parseArgs(argv);

	}catch(ArgumentParserException argExp){
	    parser.printUsage();
	    return;
	}

	File ff = new File(args.getString("filename"));

	try{
	    if(puppy.write_tr(ff))
		System.out.printf("Success\n");
	    else
		System.out.printf("Failed\n");

	}catch(ArgumentParserException argExp){
	    argExp.printStackTrace();

	}catch(IOException exp){
	    exp.printStackTrace();

	}
    }

    public static void
    print(String[] argv, FPuppy puppy, JSONObject user, BufferedReader stdin)
    {
	String[] choices = {
	    "raw",
	    "slots",
	    "job",
	    "jobs",
	    "help",
	    "pending"
	};

	ArgumentParser parser = ArgumentParsers.newFor("print").addHelp(false).build();
	parser.addArgument("command")
	    .choices(choices);


	String cmd = null;
	List<String> rest = new ArrayList<String>();

	try{
	    Namespace args = parser.parseKnownArgs(argv, rest);
	    cmd = args.get("command");
	    

	}catch(ArgumentParserException argExp){
	    parser.printUsage();
	    return;
	}

	switch(cmd)
	{
	    case "raw":
		System.out.println(
			user.toString(4)
			);
		break;

	    case "pending":
		pending(rest.toArray(new String[rest.size()]), puppy, user, stdin);
		break;

	    case "help":
		parser.printHelp();
		break;

	    case "slots":
		System.out.printf("%s slots", puppy.getSlots());
		break;

	    case "jobs": case "job":
		break;

	    default:
		// unimplemented
		break;
	}
    }

    public static void
    slots(String[] argv, FPuppy puppy, JSONObject user, BufferedReader stdin)
    {
	System.out.printf("You have %s slots", puppy.getSlots());
    }

    public static void
    tma(String[] argv, FPuppy puppy, JSONObject user, BufferedReader stdin)
    {

	System.out.println("tma executed");
    }

    public static String
    getcmd(String[] argv, FPuppy puppy, List<String> largv, BufferedReader stdin)
    {
	String[] choices = {
	    "tma",
	    "slots",
	    "print",
	    "quit",
	    "help",
	    "tfile",
	};

	ArgumentParser parser = ArgumentParsers.newFor("").addHelp(false).build();
	parser.addArgument("command")
	    .choices(choices);

	String cmd = null;

	try{
	    Namespace args = parser.parseKnownArgs(argv, largv);
	    cmd = args.get("command");

	}catch(ArgumentParserException argExp){
	    parser.printUsage();
	    return null;
	}

	switch(cmd)
	{

	    case "help":
		parser.printHelp();
		return null;

	    default:
		return cmd;

	}

    }

    public static JSONObject
    getuser(BufferedReader stdin)
	throws IOException
    {
	String uid = null, pwd = null;
	JSONObject uobj = new JSONObject();

	String line = null;

	while(uid == null || pwd == null)
	{
	    if(uid == null)
	    {

		if(line == null)
		    System.out.printf("\nuser id: ");
		else
		{
		    uid = line.trim();
		    line = null;
		    continue;
		}


	    }else if(pwd == null)
	    {
		if(line == null)
		{
		    if(!(FPuppy.user_exists(uid)))
			System.out.printf("\nnew user password: ");

		    else
			System.out.printf("\npassword: ");
		}else
		{
		    pwd = line.trim();
		    if(FPuppy.user_exists(uid) && !(FPuppy.user_exists(uid, pwd)))
		    {
			System.out.printf("\nInvalid username or password: %s, %s\n", uid, pwd);
			uid = null;
			pwd = null;
			line = null;
			// we go again
			continue;
		    }else{
			//success
			break;
		    }
		}
	    }

	    line = stdin.readLine();

	    if(line == null)
		return null;
	    else if(line.isBlank())
	    {
		System.out.println("\nBlank entry");
		line = null;
	    }

	}

	uobj.put(FPuppy.USR_ID, uid);
	uobj.put(FPuppy.USR_PWD, pwd);

	// yes, app must remember pid or pray account is successfully logged-out
	
	uobj.put(FPuppy.USR_PUPPY_ID, FPuppy.NULL_ID);
	return uobj;
    }
    
    public static void
    quit(FPuppy puppy, JSONObject user, File rc)
	throws IOException
    {
	System.out.println("\nquiting...");
	puppy.flush();
	Files.write(rc.toPath(), user.toString(4).getBytes());
	System.exit(0);
    }

    public static void
    print_welcome(FPuppy puppy, BufferedReader stdin)
	throws IOException
    {
	if(!(puppy.has_extras("fullname")))
	{
	    System.out.printf("\nFullname: ");
	    String name = stdin.readLine();
	    puppy.set_extras("fullname", (String)name);
	}

	System.out.printf("\nWelcome %s\n", puppy.get_extras("fullname"));
}

    public static void
    main(String[] argv)
	throws IOException, AuthError
    {
	BufferedReader stdin = new BufferedReader(new InputStreamReader(System.in));

	File rc = new File("./puppyrc");
	JSONObject user = null;
	FPuppy puppy;

	if(rc.exists() && rc.canRead())
	{
	    String rc_str = new String(Files.readAllBytes(rc.toPath()));
	    user = new JSONObject(rc_str);
	
	}else
	{
	    user = getuser(stdin);
	    if(user == null)
		System.exit(0);

	}

	puppy = new FPuppy(user);
	user.put(FPuppy.USR_PUPPY_ID, puppy.pid);

	print_welcome(puppy, stdin);

	String line;

	while(true)
	{
	    System.out.printf("\nIPuppy> ");
	    line = stdin.readLine();
	    if(line == null)
		quit(puppy, user, rc);

	    argv = line.split("\\s+");
	    ArrayList<String> rest = new ArrayList<String>();

	    String cmd = getcmd(argv, puppy, rest, stdin);
	    argv = rest.toArray(new String[rest.size()]);
	    if(cmd == null)
		continue;

	    switch(cmd)
	    {
		case "quit": case "exit":
		    quit(puppy, user, rc);

		case "slots":
		    slots(argv, puppy, user, stdin);
		    break;

		case "print":
		    print(argv, puppy, user, stdin);
		    break;

		case "tma":
		    tma(argv, puppy, user, stdin);
		    break;

		case "tfile":
		    tfile(argv, puppy, user, stdin);
		    break;

		default:
		    break;
	    }
	}

    }
}
