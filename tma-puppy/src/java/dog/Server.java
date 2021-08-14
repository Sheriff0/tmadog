package dog;

interface Server
{
    boolean addFile(String filename);

    boolean addFile(String filename, String data);

    boolean writeFile(String filename, String data);

    boolean updateFileJSON(String filename, org.json.JSONObject data);

    boolean writeFileJSON(String filename, org.json.JSONObject data);

    String readFile(String filename);

    org.json.JSONObject readFileJSON(String filename);
}
