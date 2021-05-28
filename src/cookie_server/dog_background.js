var CLIENT = "http://127.0.0.1:7999/dog"

var poll_timeout = 1000;

var timeout = null; 

var NOT_STARTED = true;

var get_script = null;

var NOU_URL = "https://www.nouonline.net";

var dog_win = null;
var cur_tabid = null;

var client_headers = {};
var server_headers = {};

var LOOP_READY = true;

function stop(){
	NOT_STARTED = true;
	// remove content script
	chrome.scripting.unregisterContentScript(get_script);
	get_script = null;

	window.clearTimeout(timeout);

	chrome.notifications.create({
	    "type": "basic",
	    "iconUrl": chrome.extension.getURL("dog_icon-48.png"),
	    "title": "TMADOG Cookie Server",
	    "message": "The Cookie Server has stopped"
	});
    }

function start(){
	NOT_STARTED = false;
	//chrome.scripting.registerContentScript(
	//    {
	//	"matches": [NOU_URL + "/*?*"],
	//	"js": [{"file": chrome.extension.getURL("har_getter.js")}]
	//    },
	//    function(script){
	//    get_script = script;
	//});

	//timeout = window.setTimeout(probe_client, pop_timeout);

	chrome.notifications.create({
	    "type": "basic",
	    "iconUrl": chrome.extension.getURL("dog_icon-48.png"),
	    "title": "TMADOG Cookie Server",
	    "message": "The Cookie Server has started"
	});

    //chrome.windows.create(
    //        {
    //           "type": "panel",
    //           "incognito": true,
    //           "url": "/dog_server.html"
    //        }
    //);
}


function probe_client(){
    console.log("Hello, World");
}

function handle_click(){
	if(NOT_STARTED){
	// insert content script
	//
		start();

	}else{
		stop();
}

}

//chrome.runtime.onMessage.addListener(serve_msg);

//chrome.browserAction.onClicked.addListener(start);


function rewriteHeaders(e) {
    headers = client_headers;
    for (var header of e.requestHeaders) {
	console.log(`Got header ${header.name}`);
	if (header.name.toLowerCase() in headers) {
	    console.log(`    Changing header '${header.name}' from ${header.value} to ${headers[header.name.toLowerCase()]}`);
	    header.value = headers[header.name.toLowerCase()];
	}

	server_headers[header.name] = header.value; 
    }

    return {"requestHeaders": e.requestHeaders};

}

/*
Add rewriteUserAgentHeader as a listener to onBeforeSendHeaders,
only for the target page.

Make it "blocking" so we can modify the headers.
*/

function listen_on_win(win){
    dog_win = win;
    console.log(`window created ${win}`)
}

function handle_rm(wid)
{
    console.log(`A window was removed, checking if it"s a dog window`);
    if (dog_win != null && wid == dog_win.id){
	dog_win = null;
	return serve_msg({"start": true});
    
    }

}

chrome.windows.onRemoved.addListener(handle_rm);


function listen_on_tab(tab){
    cur_tabid = tab.id;
    console.log(`tab created ${cur_tabid}`);
}


function clear_cookies_and_createtab(data)
{
    return (cookies)=>{
	for(var i=0; i<cookies.length;i++) {

	    chrome.cookies.remove(
		{
		    "url": "https://" + cookies[i].domain  + cookies[i].path,
		    "name": cookies[i].name,
		    //"firstPartyDomain": cookies[i].firstPartyDomain,
		    "storeId": cookies[i].storeId,
		},
		(ck)=> console.log(`Removed cookie ${ck.name}`),
	    );
	}

	client_headers = ("headers" in data)? data["headers"] : client_headers;

	chrome.webRequest.onBeforeSendHeaders.addListener(
	    rewriteHeaders,
	    {
		"urls": ["<all_urls>"],
	    },
	    ["blocking", "requestHeaders"]
	);

	chrome.windows.create(
	    {
		//"allowScriptsToClose": true,
		"focused": true,
		//"type": "panel",
		"url": data["url"],
	    },

	    listen_on_win
	);

    }
}

function mkcookies(data){

    chrome.cookies.getAll(
	{},
	clear_cookies_and_createtab(data),
	);

}

const handle_loop_err = (err)=>{
    console.log("got err " + String(err));
    LOOP_READY = true;
    //timeout = window.setTimeout(looper, poll_timeout);

}

const looper = ()=>{
   // to make function re-entrant 
    if (!LOOP_READY)
	return;

    LOOP_READY = false;

    console.log("started polling");
    window.fetch(CLIENT, {"mode": "no-cors"}).then((res)=>{
	return res.json();

    }).catch(handle_loop_err).then((data)=>{
	if (data && "cookies" in data){

	    window.clearTimeout(timeout);
	    mkcookies(data);
	}

	return handle_loop_err(Error("No valid request found"));
    }).catch(handle_loop_err);
}


function serve_msg(msg){
    if("cookies" in msg){
	chrome.cookies.getAll(
	    {},
	    send_to_client,
	);

    }

    if("start" in msg){
	LOOP_READY = true;
	timeout = window.setInterval(looper, poll_timeout);

    }

    if("end" in msg){
	window.clearTimeout(timeout);
    }
}

function send_to_client(cookies)
{
    pcookies = [];

    for(let cook of cookies){
	pcook = {
	    "domain": cook.domain,
	    "name": cook.name,
	    "value": cook.value,
	    "path": cook.path,
	    "rest": {
		"HttpOnly": cook.httpOnly,
	    },
	    "secure": cook.secure,
	};

	if (!cook.session)
	    pcook["expires"] = cook.expirationDate;

	pcookies.push(pcook);
    }

    body = {
	"headers": server_headers,
	"cookies": pcookies,
    };

    params = {
	"method": "POST",
	"body": JSON.stringify(body),
	"mode": "no-cors",

    };

    window.fetch(CLIENT, params).then(
	(res)=>{
	    console.log("successfully sent data to client");
	}).catch((err)=> console.log("failed to send data to server"));

    if (dog_win != null){
	//remove tab
	chrome.windows.remove(dog_win.id, ()=> {
	    dog_win = null;
	    cur_tabid = null;
	    console.log(`Removed window`)
	    serve_msg({"start": true});

	});
    }


}


chrome.runtime.onConnect.addListener(function(port) {
      port.onMessage.addListener(serve_msg);
 });


timeout = window.setInterval(looper, poll_timeout);
