
function hideControl(){
    const control = document.getElementById("control");
    control.style.display = "none";
}

function hideWaitingRoom(){
    const control = document.getElementById("waiting_room");
    control.style.display = "none";
}

function showWaitingRoom(key=""){
    hideControl()
    
    const waiting_room = document.getElementById("waiting_room");

    waiting_room.style.display = "block";

    const text = waiting_room.querySelector("#wait_message");
    const key_text = waiting_room.querySelector("#key_text");
    const start_button = waiting_room.querySelector("#start_game_button");


    if (key){
        text.textContent = "You are the host. Players can join with this code:"
        key_text.textContent = key
    }else{
        text.textContent = "Waiting for host to start the game."
        start_button.style.display = "none";
    }
}

function showGame(players){
    hideWaitingRoom()

    const play_area = document.getElementById("play_area");

    play_area.style.display = "block";

    const game_control = play_area.querySelector("#game_control")

    game_control.style.display = "block";


}

function updateGame(play_event){
    
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
                    showWaitingRoom(key=event_json.join);
                }else{
                    showWaitingRoom();
                }
                break;
            case "start_game":
                    showGame(players= event_json.num_players)
                break;
            case "play":
                    updateGame(event_json)
                break;
            default:
                log("Unknown event encountered.")

        }



    };

    socket.onclose = () => log("Socket closed");
    socket.onerror = (err) => log("Error: " + err.message);
    

    const control = document.getElementById("control");

    const start_button = control.querySelector("#start");
    const join_button = control.querySelector("#join");
    const join_field = control.querySelector("#join_text")
  


    start_button.onclick = () => {
        if (!socket || socket.readyState !== WebSocket.OPEN){
            log("Not connected to server");
            return;
        }

        socket.send(JSON.stringify({type:"init"}));


    }
    
    join_button.onclick = () => {

        const text = join_field.value.trim()
        // if (!text || (!/^[a-z0-9 ]+$/i.test(text))){
        //     log("Invalid code format");
        //     return;
        // }
        if (!socket || socket.readyState !== WebSocket.OPEN){
            log("Not connected to server");
            return;
        }
        socket.send(JSON.stringify({type:"init",join: text}));

    }


    //Waiting room


    const waiting_room = document.getElementById("waiting_room");

    const start_game_button = waiting_room.querySelector("#start_game_button");

    start_game_button.onclick = () => {
        if (!socket || socket.readyState !== WebSocket.OPEN){
            log("Not connected to server");
            return;
        }

        socket.send(JSON.stringify({type:"start_game"}));
    }

    //End waiting room

    // play area

    const play_area = document.getElementById("play_area");

    const action_buttons = play_area.querySelector("#action_buttons");

    action_buttons.addEventListener("click", (e) =>{
        if (!socket || socket.readyState !== WebSocket.OPEN){
            log("Not connected to server");
            return;
        }
        socket.send(JSON.stringify({type:"play", move: e.target.id}))

    })

    // End play area




  
});
