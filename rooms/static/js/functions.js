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
            if (this.status == 200) {
                replace('modal_text', "Successful check-in at " + room_name + ".");
            }else{
                replace('modal_text', "Could not check-in at " + room_name + ".");
            }
            $('#checkInModal').modal('show');
        }
    };

    http.send(params);

}