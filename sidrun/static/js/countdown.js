var node_containing_countdown = document.getElementById("countdown").parentNode;
var countown_text = node_containing_countdown.innerText;
var textsplit = countown_text.split("Time left or ended:");
var addbefore = "";
var addafter = "";
if (textsplit.length > 1) {
    addbefore = "<label>Time left or ended:</label><p></p>";
    countown_text = textsplit[1].trim();
    addafter = "<p></p>"
}
var time_left_splitted = countown_text.split(":");
var hours = time_left_splitted[0];
var minutes = time_left_splitted[1];
var seconds = time_left_splitted[2];
var milliseconds_left = hours * 3600 * 1000 + minutes * 60 * 1000 + seconds * 1000;
var target_date = new Date().getTime() + milliseconds_left;

// update the tag with id "node_containing_countdown" every 1 second
setInterval(function () {
    // variables for time units
    var days, hours, minutes, seconds;
    // find the amount of "seconds" between now and target
    var current_date = new Date().getTime();
    var seconds_left = (target_date - current_date) / 1000;

    // do some time calculations

    hours = parseInt(seconds_left / 3600);
    seconds_left = seconds_left % 3600;

    minutes = parseInt(seconds_left / 60);
    seconds = parseInt(seconds_left % 60);

    node_containing_countdown.innerHTML = addbefore + " " + hours + ":" + minutes + ":" + seconds + " " +addafter;

}, 1000);