import java.util.Map;
import java.util.Collection;


import net.sourceforge.argparse4j.ArgumentParsers;
import net.sourceforge.argparse4j.inf.ArgumentParser;
import net.sourceforge.argparse4j.inf.Namespace;

import net.sourceforge.argparse4j.internal.UnrecognizedArgumentException;
import net.sourceforge.argparse4j.inf.ArgumentParserException;
import net.sourceforge.argparse4j.inf.ArgumentAction;
import net.sourceforge.argparse4j.inf.Argument;

class
PAppendAction implements ArgumentAction
{
    boolean
    consumeArgument() { return true; };

    void onAttach(Argument arg) { return; };

    void
    run(ArgumentParser parser,
	    Argument arg,
	    Map<String,Object> attrs,
	    String flag, Object value)
    {
	if(!(attrs.containsKey(arg.getDest())) ||
		attrs.get(arg.getDest()) == null)
	    attrs.put(arg.getDest(), new List<Object>());

	Collection<Object> values = attrs.get(arg.getDest());

	if(value instanceof Collection)
	    values.addAll(value);

	else
	    values.add(value);
    }
}
