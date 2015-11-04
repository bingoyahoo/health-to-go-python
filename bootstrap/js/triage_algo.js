/**
 *
 * Created by Delvin on 4/11/2015.
 */
    $(document).ready(function () {
        $("#measure_button").click(function (e) {
            e.preventDefault();
            $.ajax({
                type: 'GET',
                url: "https://api.thingspeak.com/channels/61240/feeds/last?api_key=HYCPXF3T8CAJMT4X",
                dataType: 'json',
                success: function (result) {

                    var a = result['field1'];
                    var b = result['field2'];
                    $("#heart_rate").html(result['field1']);
                    $("#input_heart_rate").val(result['field1']);
                    $("#temperature").html(result['field2']);
                    $("#input_temperature").val(result['field2']);

                    function getRandomInt(min, max) {
                        return Math.floor(Math.random() * (max - min + 1)) + min;
                    }

                    var x = getRandomInt(10, 25);
                    $("#respo_rate").html(x);
                    $("#input_respo_rate").val(x);

                    var y = getRandomInt(60, 210);
                    $("#bp").html(y);
                    $("#input_bp").val(y);

                    var sum = 0;

                    function scoreHeartrate(heartbeat) {
                        if (heartbeat <= 40) {
                            return 2;
                        } else if (heartbeat <= 50) {
                            return 1;
                        } else if (heartbeat <= 100) {
                            return 0;
                        } else if (heartbeat <= 110) {
                            return 1;
                        } else if (heartbeat <= 129) {
                            return 2;
                        } else {
                            return 3;
                        }
                    }

                    function scoreTemp(temp) {
                        if (temp < 35) {
                            return 3;
                        } else if (temp <= 38.4) {
                            return 0;
                        } else {
                            return 2;
                        }
                    }

                    function scoreBP(bp) {
                        if (bp <= 70) {
                            return 3;
                        } else if (bp <= 80) {
                            return 2;
                        } else if (bp <= 100) {
                            return 1;
                        } else if (bp <= 199) {
                            return 0;
                        } else {
                            return 2;
                        }
                    }

                    function scoreRespo(respo_rate) {
                        if (respo_rate < 9) {
                            return 3;
                        } else if (respo_rate <= 14) {
                            return 1;
                        } else if (respo_rate <= 20) {
                            return 0;
                        } else if (respo_rate <= 29) {
                            return 1;
                        } else {
                            return 3;
                        }
                    }

                    sum = scoreHeartrate(a) + scoreTemp(b) + scoreRespo(x) + scoreBP(y);

                    if (sum <= 2) {
                        $("#button4").prop("checked", true)
                    } else if (sum <= 4) {
                        $("#button3").prop("checked", true)
                    } else if (sum <= 8) {
                        $("#button2").prop("checked", true)
                    } else {
                        $("#button1").prop("checked", true)
                    }
                }
            });
        });
    });
