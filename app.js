// Elementos do DOM
const ipCameraUrlInput = document.getElementById("ipCameraUrl" );
// ...

// Iniciar Câmera IP
startIpCameraBtn.addEventListener("click", async () => {
    const ipCameraUrl = ipCameraUrlInput.value;
    if (!ipCameraUrl) {
        alert("Por favor, insira a URL da câmera IP.");
        return;
    }

    try {
        const response = await fetch("/start_camera_ip", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ ipCameraUrl: ipCameraUrl })
        });
        // ... restante da lógica ...
    } catch (error) {
        // ... tratamento de erro ...
    }
});
