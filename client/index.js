
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
    const create_button = waiting_room.querySelector("#start_game_button");


    if (key){
        text.textContent = "You are the host. Players can join with this code:"
        key_text.textContent = key
    }else{
        text.textContent = "Waiting for host to start the game."
        create_button.style.display = "none";
    }
}

function initGame(players){
    hideWaitingRoom()

    const play_area = document.getElementById("play_area");

    play_area.style.display = "block";

    


}

function startTurn(){


    const game_control = play_area.querySelector("#game_control")


    game_control.style.display = "block";
    game_control.querySelector("#actions").style.display = "block";
}

function updateGame(play_event){
    
}

function sendOnSocket(socket,message){

    id = sessionStorage.getItem("id");
    token = sessionStorage.getItem("token");

    if (!socket || socket.readyState !== WebSocket.OPEN){
            log("Not connected to server");
            return;
        }
    
    
    
    const payload = Object.assign({}, message, { id, token });
    socket.send(JSON.stringify(payload));
}
const log = (msg) => {
    const el = document.getElementById("log");
    el.textContent += msg + "\n";
    };

window.addEventListener("DOMContentLoaded",()=>{

    const socket = new WebSocket("ws://localhost:8001");

    

   

    socket.onmessage = (event) => {
        log(event.data)
        const event_json = JSON.parse(event.data);
        
        switch(event_json.type){
            case "init":
                sessionStorage.setItem("token" , event_json.token)
                sessionStorage.setItem("id", event_json.id)
                sessionStorage.setItem("colour", event_json.colour)
                sessionStorage.setItem("name", event_json.name)
                if (event_json.join){ //you are the host
                    showWaitingRoom(key=event_json.join);
                }else{
                    showWaitingRoom(); //you are a guest
                }
                break;
            case "start_game":
                    initGame(players= event_json.num_players)
                break;
            case "input_request":
                if (event_json["input_type"] == "action"){
                    startTurn()
                }
                break;
            case "play":
                    updateGame(event_json)
                break;
            default:
                break;
        }



    };

    socket.onclose = () => log("Socket closed");
    socket.onerror = (err) => log("Error: " + err.message);
    

    const control = document.getElementById("control");

    const create_button = control.querySelector("#create");
    const join_button = control.querySelector("#join");
    const join_field = control.querySelector("#join_text")
    const player_name_text = control.querySelector("#player_name_text")


    create_button.onclick = () => {


        

        const name = player_name_text.value.trim()

        
        sendOnSocket(socket,{type:"init", player_name:name})
        


    }
    
    join_button.onclick = () => {

       

        const text = join_field.value.trim()
        const name = player_name_text.value.trim()

        // if (!text || (!/^[a-z0-9 ]+$/i.test(text))){
        //     log("Invalid code format");
        //     return;
        // }
        
        sendOnSocket(socket,{type:"init",join: text, player_name:name});

    }


    //Waiting room


    const waiting_room = document.getElementById("waiting_room");

    const start_game_button = waiting_room.querySelector("#start_game_button");

    start_game_button.onclick = () => {
        

        sendOnSocket(socket,{type:"start_game"});
    }

    //End waiting room

    // play area

    const play_area = document.getElementById("play_area");

    const action_buttons = play_area.querySelector("#action_buttons");

    action_buttons.addEventListener("click", (e) =>{
        sendOnSocket(socket,{type:"input_fulfill", move: e.target.id});
    })

    // End play area




  
});
