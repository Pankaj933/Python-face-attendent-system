let attendanceStream = null;
let attendanceScanActive = false;

function goToDashboard() {
    window.location.assign("/");
}

document.addEventListener("DOMContentLoaded", () => {
    startAttendanceCamera();
});


// ==========================================
// START ATTENDANCE CAMERA
// ==========================================

async function startAttendanceCamera() {

    if (attendanceStream) {
        return;
    }

    const video = document.getElementById("video");
    const message = document.getElementById("cameraMessage");

    try {

        attendanceStream =
            await navigator.mediaDevices.getUserMedia({

                video: {
                    width: {
                        ideal: 1280
                    },

                    height: {
                        ideal: 720
                    },

                    facingMode: "user"
                },

                audio: false

            });


        video.srcObject = attendanceStream;

        message.innerText = "Camera is running";
        message.style.color = "green";

        if (!attendanceScanActive) {
            attendanceScanActive = true;
            runAttendanceDetection();
        }


    } catch (error) {

        console.error("Camera Error:", error);

        message.innerText =
            "Camera access nahi mila.";

        message.style.color = "red";
    }
}

async function runAttendanceDetection() {
    while (attendanceStream) {
        const attendanceMarked = await checkAttendance();

        if (attendanceMarked) {
            return;
        }

        await new Promise(resolve => setTimeout(resolve, 1500));
    }

    attendanceScanActive = false;
}


// ==========================================
// CHECK ATTENDANCE
// ==========================================

async function checkAttendance() {

    const video =
        document.getElementById("video");

    const canvas =
        document.getElementById("canvas");

    const message =
        document.getElementById("attendanceMessage");

    const resultName =
        document.getElementById("resultName");

    const resultDetails =
        document.getElementById("resultDetails");


    // ======================================
    // CAMERA CHECK
    // ======================================

    if (!attendanceStream) {

        message.innerText =
            "Camera start nahi hai. Retry Camera par click karo.";

        message.style.color = "red";

        return;
    }


    if (
        video.videoWidth === 0 ||
        video.videoHeight === 0
    ) {

        message.innerText =
            "Camera frame ready nahi hai.";

        message.style.color = "red";

        return;
    }


    // ======================================
    // CAPTURE FRAME
    // ======================================

    canvas.width =
        video.videoWidth;

    canvas.height =
        video.videoHeight;


    const context =
        canvas.getContext("2d");


    context.drawImage(
        video,
        0,
        0,
        canvas.width,
        canvas.height
    );


    const imageData =
        canvas.toDataURL(
            "image/jpeg",
            0.9
        );


    message.innerText =
        "Face checking...";

    message.style.color =
        "orange";


    resultName.innerText =
        "Checking face...";

    resultDetails.innerText =
        "Please wait.";


    // ======================================
    // SEND TO FLASK
    // ======================================

    try {

        const response =
            await fetch(
                "/api/check-attendance",
                {

                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        image: imageData
                    })

                }
            );


        const result =
            await response.json();


        console.log(
            "Attendance API Response:",
            result
        );


        // ==================================
        // SUCCESS
        // ==================================

        if (result.success) {

            const user =
                result.user;


            message.innerText =
                "✅ " + result.message;

            message.style.color =
                "green";


            resultName.innerText =
                user.name;


            resultDetails.innerText =
                "Employee ID: " +
                user.employee_id +
                " | " +
                "Department: " +
                (user.department || "N/A") +
                " | " +
                "Time: " +
                (result.time || "Already marked");


            // Already marked bhi success hai
            if (result.already_marked) {

                message.innerText =
                    "ℹ️ " + result.message;

                message.style.color =
                    "orange";
            } else {
                const successModal =
                    document.getElementById("attendanceSuccessModal");

                const successDetails =
                    document.getElementById("attendanceSuccessDetails");

                successDetails.innerText =
                    "Name: " + user.name +
                    " | Employee ID: " + user.employee_id +
                    " | Department: " + (user.department || "N/A") +
                    " | Date: " + result.date +
                    " | Time: " + result.time +
                    " | Status: Present";

                successModal.hidden = false;

                successModal
                    .querySelector(".attendance-modal-ok")
                    .focus();
            }

            return true;

        } else {

            // ==================================
            // FAILURE
            // ==================================

            message.innerText =
                "❌ " + result.message;

            message.style.color =
                "red";


            resultName.innerText =
                "Attendance not marked";


            resultDetails.innerText =
                result.message;


            // Score available ho to show karo
            if (result.score !== undefined) {

                resultDetails.innerText =
                    result.message +
                    " | Match Score: " +
                    result.score;
            }

            if (result.message === "Face detect nahi hua.") {
                message.innerText =
                    "Camera ke saamne apna face rakhein...";
                message.style.color = "orange";
            }

            return false;
        }


    } catch (error) {

        console.error(
            "Attendance Request Error:",
            error
        );


        message.innerText =
            "❌ Server connection error.";

        message.style.color =
            "red";


        resultName.innerText =
            "Server Error";


        resultDetails.innerText =
            "Attendance API se connection nahi ho paaya.";

        return false;
    }
}