function replace(id, text) {
    document.getElementById(id).innerHTML = text;
}

function check_in(room_id, room_name) {

    var http = new XMLHttpRequest();
    var url = "/room4u/check-in/new";
    var params = "room=" + room_id;

    http.open("POST", url, true);
    http.setRequestHeader("Content-type", "application/x-www-form-urlencoded");

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

    http.send(params);
}

function check_out() {
    var http = new XMLHttpRequest();
    var url = "/room4u/check-out";

    http.open("POST", url, true);
    http.setRequestHeader("Content-type", "application/x-www-form-urlencoded");

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

    http.send();

}


$("#newmessage").submit(function(event) {


    /* stop form from submitting normally */
    event.preventDefault();
    $('#messageModal').modal('hide');

    /* get the action attribute from the <form action=""> element */
    var $form = $(  this );//, url = $form.attr( 'action' );
    var url = "/room4u/messages/handler"
    var http = new XMLHttpRequest();
    var subject = $('#subject').val();
    var message = $('#message').val();
    var destination = $('#destination').val();
    var destflag = $('#destflag').val();
    var params = "subject=" + subject.toString() + "&message=" + message.toString() + "&destination=" + destination.toString() + "&destflag=" + destflag.toString();

    /*var posting = $.post( url, { rname: $('#rname').val(), subject: $('#subject').val(), message: $('#message').val()} );

     /* Alerts the results */
    /*posting.done(function( data ) {
     alert('success');
     });*/
    http.open("POST", url, true);
    http.setRequestHeader("Content-type", "application/x-www-form-urlencoded");

    http.onreadystatechange = function () {
        if (this.readyState == 4) {
            replace('alertModalLabel', "New Message");
            replace('but', "Return To Messages");
            document.getElementById('but').onclick = function(){
                window.location.href = "/room4u/messages";
            }

            if (this.status == 200) {
                replace('alertModalText', "Message sent");
            }else{
                replace('alertModalText', "Could not send the message. Try again later");
            }
            $('#alertModal').modal('show');
        }
    };
    http.send(params);

});

function newMessageForm(destination) {
    document.getElementById("destination").value=destination;
    document.getElementById("destflag").value="room";
    $('#messageModal').modal('show');
}

function newMessageForm2(destination) {
    document.getElementById("destination").value=destination;
    document.getElementById("destflag").value="user";
    $('#messageModal').modal('show');
}

function income() {
    $.ajax({
        url:'/room4u/messages/incoming',
        type:"POST",
        success:function(data){  // success is the callback when the server
            if (data != "nothing"){
                var message = JSON.parse(data);
                replace('alertModalLabel', "Message Received");
                replace('but', "Ok");
                replace('alertModalText', message[0].fields.text);
                $('#alertModal').modal('show');
            }
        }
    });
}

income(); // This will run on page load
setInterval(function(){
    income() // this will run after every 5 seconds
}, 5000);