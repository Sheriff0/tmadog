package dog;

import java.io.File;
import java.nio.file.Files;
import java.nio.file.Path;
import java.io.IOException;

class
FileServer extends Server
{
    private File _dir;

    FileServer()
    {
	_dir = File(".");
    }

    FileServer(String dir)
    throws NoDirNoRead, NoFileNoCreate
    {
	File ff = File(dir);

	if(!(ff.exists()) && !(ff.mkdirs()))
	    throw new NoFileNoCreate(
		    String.format("the directory '%s' does not exist or can't be created", ff);
		    );

	else if(!(ff.isDirectory()) || !(ff.canRead()))
		throws new NoDirNoRead(
			String.format("the file '%s' is not a directory or can't be read", ff);
			);

	this._dir = ff;
    }

    String
    get(String path)
    {
	return read(path);
    }

    String
    read(String path)
    {
	Path file = File(this._dir, path).toPath();
	try
	{
	    return new String(Files.readAllBytes(file));
	
	}catch(IOException exp)
	{
	    return null;
	}
    }
    
    Integer
    put(String path, String data)
    {
	return write(path, data);
    }

    Integer
    post(String path, String data)
    {
	return write(path, data);
    }

    // returns number of bytes written
    Integer
    write(String path, String data)
    {

	Path file = File(this._dir, path).toPath();
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
