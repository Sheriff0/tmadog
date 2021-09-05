package dog;

class
Dropbox/* extends Server*/
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

}
