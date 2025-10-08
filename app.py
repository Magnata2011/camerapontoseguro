from flask import Flask, render_template, request, jsonify
import cv2
import numpy as np
import base64

app = Flask(__name__)

# Definir a faixa de cor laranja para o botão (exemplo, pode precisar de ajuste)
# Estes valores são para HSV (Hue, Saturation, Value)
LOWER_ORANGE = np.array([5, 100, 100])
UPPER_ORANGE = np.array([15, 255, 255])

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/process-frame", methods=["POST"])
def process_frame():
    data = request.get_json()
    image_data = data["imageData"]
    timestamp = data["timestamp"]

    # Remover o prefixo 'data:image/jpeg;base64,'
    base64_image = image_data.split(",")[1]
    
    # Decodificar a imagem base64
    img_bytes = base64.b64decode(base64_image)
    
    # Converter bytes para array numpy e depois para imagem OpenCV
    np_arr = np.frombuffer(img_bytes, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if frame is None:
        return jsonify({"error": "Could not decode image"}), 400

    hand_proximity_status = "longe"
    detection_message = "Nenhuma detecção."
    button_bbox = None # Bounding box do botão [x, y, w, h]

    # 1. Detecção do Botão (baseado em cor)
    hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv_frame, LOWER_ORANGE, UPPER_ORANGE)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if contours:
        # Encontrar o maior contorno (assumindo que é o botão)
        largest_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest_contour)
        
        if w > 20 and h > 20: # Filtrar pequenos ruídos, garantir tamanho mínimo
            button_bbox = [int(x), int(y), int(w), int(h)]
            detection_message = "Botão detectado."

            # 2. Simulação de Detecção de Mão e Proximidade
            # Esta é uma simulação. Em um cenário real, você usaria um modelo de detecção de mão
            # e calcularia a distância real da mão ao botão.
            time_in_ms = int(timestamp)
            if time_in_ms % 10000 < 3000: # Simula 'no meio' por 3 segundos a cada 10 segundos
                hand_proximity_status = "no meio"
                detection_message = "Mão no meio do botão (simulado)!"
            elif time_in_ms % 10000 < 6000: # Simula 'quase' por 3 segundos a cada 10 segundos
                hand_proximity_status = "quase"
                detection_message = "Mão quase pressionando o botão (simulado)!"
            else:
                hand_proximity_status = "longe"
                detection_message = "Mão longe do botão (simulado)."

    response = {
        "handProximityStatus": hand_proximity_status,
        "message": detection_message,
        "timestamp": timestamp,
        "buttonBbox": button_bbox
    }

    return jsonify(response)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

