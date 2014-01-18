var lock = false;
var message_count = 0;
var sid = 0;

function update_messages(data) {
    var messages = data[0][0];
    message_count = data[0][1];
    if (messages != null) {
        $('#message').append(messages);
        $(".temp").hide();
        $(".temp:last").show();
        var objDiv = document.getElementById("scrollable");
        objDiv.scrollTop = objDiv.scrollHeight;
    }
}

function update_players(data) {
    var players = data[1];
    if (players != null) {
        $("div#players").html(players);
    }
}

function update_form(data) {
    var form = data[2];
    if (form != null) {
        $("div#form").html(form);
    }
}

function update() {
    if(!lock) {
        lock = true;
        $.ajax({
            type: "POST",
            url: "/update",
            data: { 
                'username': username,
                'message_count': message_count,
                'sid': sid,
            },
            dataType: "json",
                    
            success: function(data){

                update_messages(data);
                update_players(data);
                update_form(data);
                sid = data[3];
                lock = false;
            },
        });
    } else {
        setTimeout(update, 1500);
    }
}

function send(type) {
    $.ajax({
        type: "POST",
        url: "/process/" + username,
        data: $("form").serialize() + "&type=" + type,
        dataType: "json",
                
        success: function(data){
            update();
        },
    });
}