let stream = null;


// ===============================
// START CAMERA
// ===============================

async function startCamera() {

    const video = document.getElementById("video");
    const message = document.getElementById("cameraMessage");

    try {

        stream = await navigator.mediaDevices.getUserMedia({
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

        video.srcObject = stream;

        message.innerText = "Camera is running";

        message.style.color = "green";

    } catch (error) {

        console.error(error);

        message.innerText =
            "Camera access nahi mila. Browser permission check karo.";

        message.style.color = "red";
    }
}


// ===============================
// CAPTURE FACE
// ===============================

async function captureFace() {

    const video = document.getElementById("video");
    const canvas = document.getElementById("canvas");
    const message = document.getElementById("captureMessage");

    if (!stream) {

        message.innerText =
            "Pehle Open Camera button par click karo.";

        message.style.color = "red";

        return;
    }


    if (video.videoWidth === 0 || video.videoHeight === 0) {

        message.innerText =
            "Camera frame abhi ready nahi hai.";

        message.style.color = "red";

        return;
    }


    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;


    const context = canvas.getContext("2d");

    context.drawImage(
        video,
        0,
        0,
        canvas.width,
        canvas.height
    );


    // Canvas image ko Base64 mein convert karo

    const imageData = canvas.toDataURL("image/jpeg", 0.9);


    message.innerText =
        "Face checking...";

    message.style.color = "orange";


    try {

        const response = await fetch(
            "/api/detect-face",
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    image: imageData
                })
            }
        );


        const result = await response.json();


        if (result.success) {

            message.innerText =
                "✅ " + result.message;

            message.style.color = "green";

            console.log("Face detected successfully.");

        } else {

            message.innerText =
                "❌ " + result.message;

            message.style.color = "red";
        }


    } catch (error) {

        console.error(error);

        message.innerText =
            "❌ Server se connection nahi ho paaya.";

        message.style.color = "red";
    }
}
async function registerUser() {

    const name = document.getElementById("name").value.trim();
    const employeeId = document.getElementById("employee_id").value.trim();
    const email = document.getElementById("email").value.trim();
    const phone = document.getElementById("phone").value.trim();
    const department = document.getElementById("department").value.trim();

    const canvas = document.getElementById("canvas");
    const video = document.getElementById("video");
    const message = document.getElementById("captureMessage");


    // ===============================
    // VALIDATION
    // ===============================

    if (!name) {

        message.innerText = "Name enter karo.";
        message.style.color = "red";

        return;
    }


    if (!employeeId) {

        message.innerText = "Employee ID enter karo.";
        message.style.color = "red";

        return;
    }


    if (!stream) {

        message.innerText =
            "Pehle camera open karo.";

        message.style.color = "red";

        return;
    }


    if (video.videoWidth === 0) {

        message.innerText =
            "Camera frame ready nahi hai.";

        message.style.color = "red";

        return;
    }


    // ===============================
    // CAPTURE CURRENT FRAME
    // ===============================

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const context = canvas.getContext("2d");

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
        "Registering user...";

    message.style.color = "orange";


    try {

        const response = await fetch(
            "/api/register-user",
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({

                    name: name,

                    employee_id:
                        employeeId,

                    email: email,

                    phone: phone,

                    department:
                        department,

                    image: imageData

                })
            }
        );


        const result =
            await response.json();


        if (result.success) {

    message.innerText =
        "✅ " + result.message;

    message.style.color = "green";


    console.log(
        "Registered User ID:",
        result.user_id
    );


    // Dashboard par redirect
    setTimeout(() => {

        window.location.href = "/";

    }, 1000);

} else {

            message.innerText =
                "❌ " + result.message;

            message.style.color =
                "red";
        }


    } catch (error) {

        console.error(error);

        message.innerText =
            "❌ Server connection error.";

        message.style.color =
            "red";
    }
}