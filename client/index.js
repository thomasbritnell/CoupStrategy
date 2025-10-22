
function hideControl(){
    const control = document.getElementById("control");
    control.style.display = "none";
}

function showWaitingRoom(key=""){
    hideControl()
    
    const waiting_room = document.getElementById("waiting_room");
    const text = waiting_room.querySelector("#wait_message");
    const key_text = waiting_room.querySelector("#key_text");

    if (key){
        text.textContent = "You are the host. Players can join with this code:"
        key_text.textContent = key
    }else{
        text.textContent = "Waiting for host to start the game."
    }
}



window.addEventListener("DOMContentLoaded",()=>{

    const socket = new WebSocket("ws://localhost:8001");

    const log = (msg) => {
    const el = document.getElementById("log");
    el.textContent += msg + "\n";
    };

   

    socket.onmessage = (event) => {
        log(event.data)
        const event_json = JSON.parse(event.data);

        switch(event_json.type){
            case "init":
                if (event_json.join){
                    showWaitingRoom(key=event.join);
                }else{
                    showWaitingRoom();
                }
                break;
            default:
                log("Unknown event encountered.")

        }



    };

    socket.onclose = () => log("Socket closed");
    socket.onerror = (err) => log("Error: " + err.message);
    

    const control = document.getElementById("control");

    const start_button = Object.assign(document.createElement("button"), {id:"start", textContent:"start new game"});
    const join_button = Object.assign(document.createElement("button"), {id:"join", textContent:"join a game"});
    const join_field = Object.assign(document.createElement("input"),{id:"join_text", type:"text"})
  


    start_button.onclick = () => {
        if (!socket || socket.readyState !== WebSocket.OPEN){
            log("Not connected to server");
            return;
        }

        socket.send(JSON.stringify({type:"init"}));


    }
    
    join_button.onclick = () => {

        const text = join_field.value.trim()
        if (!text || (!/^[a-z0-9 ]+$/i.test(text))){
            log("Invalid code format");
            return;
        }
        if (!socket || socket.readyState !== WebSocket.OPEN){
            log("Not connected to server");
            return;
        }

        socket.send(JSON.stringify({type:"init",join: text}));

    }
    


    control.appendChild(start_button)
    control.appendChild(join_button)
    control.appendChild(join_field)


  
});
