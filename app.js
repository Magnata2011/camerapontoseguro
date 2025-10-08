document.addEventListener('DOMContentLoaded', () => {
    // Elementos do DOM
    const video = document.getElementById("video");
    const canvas = document.getElementById("canvas");
    const ctx = canvas.getContext("2d");
    const overlayCanvas = document.getElementById("overlayCanvas");
    const overlayCtx = overlayCanvas.getContext("2d");
    const startBtn = document.getElementById("startBtn");
    const stopBtn = document.getElementById("stopBtn");
    const detectBtn = document.getElementById("detectBtn");
    const cameraStatus = document.getElementById("cameraStatus");
    const detectionStatus = document.getElementById("detectionStatus");
    const frameCount = document.getElementById("frameCount");
    const proximityStatus = document.getElementById("proximityStatus");
    const alertDiv = document.getElementById("alert");

    // Variáveis de controle
    let stream = null;
    let detectionInterval = null;
    let frameCounter = 0;
    let isDetecting = false;

    // Iniciar câmera
    startBtn.addEventListener("click", async () => {
        try {
            stream = await navigator.mediaDevices.getUserMedia({ 
                video: { 
                    width: 640, 
                    height: 480 
                } 
            });
            video.srcObject = stream;
            
            // Aguardar o vídeo carregar para obter as dimensões corretas
            video.addEventListener("loadedmetadata", () => {
                overlayCanvas.width = video.videoWidth;
                overlayCanvas.height = video.videoHeight;
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
            });
            
            cameraStatus.textContent = "Ligada";
            startBtn.disabled = true;
            stopBtn.disabled = false;
            detectBtn.disabled = false;
            
            console.log("Câmera iniciada com sucesso");
        } catch (error) {
            console.error("Erro ao acessar a câmera:", error);
            alert("Erro ao acessar a câmera. Verifique as permissões.");
        }
    });

    // Parar câmera
    stopBtn.addEventListener("click", () => {
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
            video.srcObject = null;
            stream = null;
            
            if (detectionInterval) {
                clearInterval(detectionInterval);
                detectionInterval = null;
                isDetecting = false;
            }
            
            // Limpar o canvas de overlay
            overlayCtx.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);
            
            cameraStatus.textContent = "Desligada";
            detectionStatus.textContent = "Inativa";
            proximityStatus.textContent = "-";
            startBtn.disabled = false;
            stopBtn.disabled = true;
            detectBtn.disabled = true;
            detectBtn.textContent = "Iniciar Detecção";
            alertDiv.classList.remove("show");
            
            console.log("Câmera parada");
        }
    });

    // Iniciar/parar detecção
    detectBtn.addEventListener("click", () => {
        if (!isDetecting) {
            // Iniciar detecção
            isDetecting = true;
            detectionStatus.textContent = "Ativa";
            detectBtn.textContent = "Parar Detecção";
            
            // Processar frames a cada 500ms
            detectionInterval = setInterval(processFrame, 500);
            
            console.log("Detecção iniciada");
        } else {
            // Parar detecção
            isDetecting = false;
            detectionStatus.textContent = "Inativa";
            detectBtn.textContent = "Iniciar Detecção";
            
            if (detectionInterval) {
                clearInterval(detectionInterval);
                detectionInterval = null;
            }
            
            // Limpar o canvas de overlay
            overlayCtx.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);
            proximityStatus.textContent = "-";
            alertDiv.classList.remove("show");
            
            console.log("Detecção parada");
        }
    });

    // Processar frame
    async function processFrame() {
        if (!video.videoWidth || !video.videoHeight) {
            console.log("Vídeo ainda não está pronto");
            return;
        }
        
        // Desenhar o frame atual no canvas
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        
        // Converter canvas para base64
        const imageData = canvas.toDataURL("image/jpeg", 0.8);
        
        // Incrementar contador de frames
        frameCounter++;
        frameCount.textContent = frameCounter;
        
        try {
            // Enviar frame para o backend
            // ATENÇÃO: Se você estiver hospedando o HTML no GitHub Pages e o backend em outro lugar,
            // você precisará substituir "/process-frame" pela URL completa do seu backend (ex: "https://seu-backend.com/process-frame" ).
            const response = await fetch("/process-frame", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    imageData: imageData,
                    timestamp: Date.now()
                })
            });
            
            if (!response.ok) {
                throw new Error("Erro na resposta do servidor");
            }
            
            const result = await response.json();
            
            // Limpar o canvas de overlay antes de desenhar
            overlayCtx.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);
            
            // Desenhar a caixa azul ao redor do botão, se detectado
            if (result.buttonBbox) {
                const [x, y, w, h] = result.buttonBbox;
                
                // Desenhar retângulo azul
                overlayCtx.strokeStyle = "#0000FF"; // Azul
                overlayCtx.lineWidth = 3;
                overlayCtx.strokeRect(x, y, w, h);
                
                // Desenhar texto colorido acima da caixa
                let textColor = "#FF0000"; // Vermelho (longe)
                let textMessage = "Longe";
                
                if (result.handProximityStatus === "no meio") {
                    textColor = "#00FF00"; // Verde (no meio)
                    textMessage = "No Meio";
                } else if (result.handProximityStatus === "quase") {
                    textColor = "#FFA500"; // Laranja (quase)
                    textMessage = "Quase";
                }
                
                overlayCtx.font = "bold 20px Arial";
                overlayCtx.fillStyle = textColor;
                overlayCtx.fillText(textMessage, x, y - 10);
                
                // Atualizar status de proximidade na interface
                proximityStatus.textContent = textMessage;
                proximityStatus.style.color = textColor;
            }
            
            // Verificar se há detecção de mão próxima ao botão para o alerta
            if (result.handProximityStatus === "no meio" || result.handProximityStatus === "quase") {
                alertDiv.classList.add("show");
                console.log("Mão detectada próxima ao botão!", result.message);
            } else {
                alertDiv.classList.remove("show");
            }
            
            console.log("Frame processado:", result);
            
        } catch (error) {
            console.error("Erro ao processar frame:", error);
        }
    }

    // Limpar recursos quando a página for fechada
    window.addEventListener("beforeunload", () => {
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
        }
        if (detectionInterval) {
            clearInterval(detectionInterval);
        }
    });
});

