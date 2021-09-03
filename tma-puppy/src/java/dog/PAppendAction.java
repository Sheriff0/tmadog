package dog;

import java.util.Map;
import java.util.Collection;
import java.util.List;
import java.util.ArrayList;


import net.sourceforge.argparse4j.ArgumentParsers;
import net.sourceforge.argparse4j.inf.ArgumentParser;
import net.sourceforge.argparse4j.inf.Namespace;

import net.sourceforge.argparse4j.internal.UnrecognizedArgumentException;
import net.sourceforge.argparse4j.inf.ArgumentParserException;
import net.sourceforge.argparse4j.inf.ArgumentAction;
import net.sourceforge.argparse4j.inf.Argument;

public class
PAppendAction implements ArgumentAction
{
    public boolean
    consumeArgument() { return true; };

    public void onAttach(Argument arg) { return; };

    public void
    run(ArgumentParser parser,
	    Argument arg,
	    Map<String,Object> attrs,
	    String flag, Object value)
    {
	if(!(attrs.containsKey(arg.getDest())) ||
		attrs.get(arg.getDest()) == null)
	    attrs.put(arg.getDest(), new ArrayList<Object>());

	Collection<Object> values = (Collection<Object>)attrs.get(arg.getDest());

	if(value instanceof Collection)
	    values.addAll((Collection<Object>)value);

	else
	    values.add(value);
    }
}
