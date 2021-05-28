var port = chrome.extension.connect({
      name: "cookie connect"
 });

port.postMessage({"cookies": true});

//port.onMessage.addListener(function(msg) {
//  console.log("message recieved" + msg);
//});
//window.close();
