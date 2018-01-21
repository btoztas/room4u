function replace(id, text) {
    document.getElementById(id).innerHTML = text;
}

function check_in(room, room_name, user) {

    var http = new XMLHttpRequest();
    var url = "/room4u/api/visits";
    var params = {
        "room": room,
        "user": user
    };

    http.open("POST", url, true);
    http.setRequestHeader("Content-type", "application/json");

    http.onreadystatechange = function () {

        if (this.readyState == 4) {
            replace('alertModalLabel', "Check-in Status");
            if (this.status == 200) {
                replace('alertModalText', "Successful check-in at " + room_name + ".");
            }
            else if (this.status == 409) {
                replace('alertModalText', "You are already checked-in at " + room_name + ".");
            } else {
                replace('alertModalText', "Could not check-in at " + room_name + ".");
            }
            $('#alertModal').modal('show');
        }
    };

    http.send(JSON.stringify(params));
}

function check_out(room, user) {
    var http = new XMLHttpRequest();
    var url = "/room4u/api/visits";

    http.open("PUT", url, true);
    http.setRequestHeader("Content-type", "application/json");
    var params = {
        "room": room,
        "user": user
    };

    http.onreadystatechange = function () {

        if (this.readyState == 4) {
            replace('alertModalLabel', "Check-out Status");
            if (this.status == 200) {
                replace('alertModalText', "Checked-out with success.");
            } else {
                replace('alertModalText', "Could not check-out.");
            }
            $('#alertModal').modal('show');
        }
    };

    http.send(JSON.stringify(params));

}


$("#newmessage").submit(function(event) {


    /* stop form from submitting normally */
    //$('#alertModal').modal('show');
    event.preventDefault();
    if($('#subject').val()=='' || $('#message').val()==''){
        replace('messageModalLabel', "Message must have subject and body");
        $('#messageModal').modal('show');
    }else {
        /* get the action attribute from the <form action=""> element */
        var $form = $(this);//, url = $form.attr( 'action' );
        var url = "/room4u/api/messages/";
        var http = new XMLHttpRequest();
        var subject = $('#subject').val();
        var message = $('#message').val();
        var destination = $('#destination').val();
        var destflag = $('#destflag').val();
        var sender = $('#sender').val();
        if (destflag == "user") {
            var params = {
                "subject": subject.toString(),
                "message": message.toString(),
                "sender_id": sender.toString(),
                "user": destination.toString()
            };
        } else {
            var params = {
                "subject": subject.toString(),
                "message": message.toString(),
                "sender_id": sender.toString(),
                "room": destination.toString()
            };
        }
        /*var posting = $.post( url, { rname: $('#rname').val(), subject: $('#subject').val(), message: $('#message').val()} );

         /* Alerts the results */
        /*posting.done(function( data ) {
         alert('success');
         });*/
        http.open("POST", url, true);
        http.setRequestHeader("Content-type", "application/json");
        http.onreadystatechange = function (data) {
            if (this.readyState == 4) {
                replace('alertModalLabel', "New Message");
                replace('but', "Return To Messages");
                document.getElementById('but').onclick = function () {
                    window.location.href = "/room4u/messages";
                }
                if (this.status == 200) {
                    $('#messageModal').modal('hide');
                    replace('alertModalText', "Message sent");
                } else {
                    $('#messageModal').modal('hide');
                    replace('alertModalText', "Could not send the message. Try again later");
                }
                $('#alertModal').modal('show');
            }
        };
        http.send(JSON.stringify(params));
    }

});

function newMessageForm(destination) {
    document.getElementById("destination").value = destination;
    document.getElementById("destflag").value = "room";
    replace('messageModalLabel', "New Message");
    $('#messageModal').modal('show');
}

function newMessageForm2(destination) {
    document.getElementById("destination").value = destination;
    document.getElementById("destflag").value = "user";
    replace('messageModalLabel', "New Message");
    $('#messageModal').modal('show');
}

function income() {
    var base_url = '/room4u/api/users/';
    var url = base_url.concat($('#receiver').val(), "/new_messages")
    $.ajax({
        url:url,
        type:"DELETE",
        success:function(data){  // success is the callback when the server
            if (data.toString() != ''){
                replace('alertModalLabel', data[0].fields.title);
                replace('but', "Ok");
                replace('alertModalText', data[0].fields.text);
                $('#alertModal').modal('show');
            }
        }
    });
}

income(); // This will run on page load
setInterval(function(){
    income() // this will run after every 5 seconds
}, 5000);