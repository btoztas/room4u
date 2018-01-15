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
            }else{
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
            }else{
                replace('alertModalText', "Could not check-out.");
            }
            $('#alertModal').modal('show');
        }
    };

    http.send();

}