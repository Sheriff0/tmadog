package dog;

class Dropbox implements Server
{
    final static String UPLOAD_URL = "https://content.dropboxapi.com/2/files/upload";

    final static String DOWNLOAD_URL = "https://content.dropboxapi.com/2/files/download";

    final static String DELETE_URL = "https://api.dropboxapi.com/2/files/delete";

    final static String LIST_URL = "https://api.dropboxapi.com/2/files/list_folder";

    private String _key;

    Dropbox()
    {
	_key = "zxK60VpMtmwAAAAAAAAAAZ76lD62i4GvL5SxC9ZgkQpIrpV4cReqSh0-SoujeAtZ";
    }

    Dropbox(String key)
    {
	_key = key;
    }

    boolean addFile(String filename);

    boolean addFile(String filename, String data);

    boolean writeFile(String filename, String data);

    boolean updateFileJSON(String filename, org.json.JSONObject data);

    boolean writeFileJSON(String filename, org.json.JSONObject data);

    String readFile(String filename);

    org.json.JSONObject readFileJSON(String filename);
}
