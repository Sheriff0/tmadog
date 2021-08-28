package dog;

import java.io.File;
import java.nio.file.Files;
import java.nio.file.Path;
import java.io.IOException;

class
FileServer extends Server
{
    private final File _dir;

    FileServer()
    {
	this._dir = new File(".");
    }

    FileServer(String dir)
    throws NoDirNoRead, NoFileNoCreate
    {
	File ff = new File(dir);

	if(!(ff.exists()) && !(ff.mkdirs()))
	{
	    throw new NoFileNoCreate(
		    String.format("the directory '%s' does not exist or can't be created", ff)
		    );

	}else if(!(ff.isDirectory()) || !(ff.canRead()))
	{
		throw new NoDirNoRead(
			String.format("the file '%s' is not a directory or can't be read", ff)
			);
	}

	this._dir = ff;
    }

    public String
    get(String path)
    {
	return read(path);
    }

    public String
    read(String path)
    {
	Path file = new File(this._dir, path).toPath();
	try
	{
	    return new String(Files.readAllBytes(file));
	
	}catch(IOException exp)
	{
	    return null;
	}
    }
    
    public Integer
    put(String path, String data)
    {
	return write(path, data);
    }

    public Integer
    post(String path, String data)
    {
	return write(path, data);
    }

    // returns number of bytes written
    Integer
    write(String path, String data)
    {

	Path file = new File(this._dir, path).toPath();
	try
	{
	    byte[] bytes = data.getBytes();
	    Files.write(file, bytes);
	    return bytes.length;
	
	}catch(IOException exp)
	{
	    return -1;
	}
    }
}
