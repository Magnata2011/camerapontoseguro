from flask import Flask, render_template, request, Response, jsonify
import cv2
import numpy as np
import base64
import time

app = Flask(__name__)

# Definir a faixa de cor laranja para o botão (exemplo, pode precisar de ajuste)
# Estes valores são para HSV (Hue, Saturation, Value)
LOWER_ORANGE = np.array([5, 100, 100])
UPPER_ORANGE = np.array([15, 255, 255])

# Variável global para armazenar o objeto VideoCapture
# Isso permite que o stream seja acessado por diferentes rotas e funções
camera = None

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/start_camera_ip", methods=["POST"])
def start_camera_ip():
    global camera
    data = request.get_json()
    ip_camera_url = data.get("ipCameraUrl")

    if not ip_camera_url:
        return jsonify({"status": "error", "message": "URL da câmera IP não fornecida."}), 400

    if camera is not None and camera.isOpened():
        camera.release()

    try:
        camera = cv2.VideoCapture(ip_camera_url)
        if not camera.isOpened():
            raise IOError("Não foi possível abrir o stream da câmera IP.")
        return jsonify({"status": "success", "message": "Câmera IP iniciada com sucesso."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/stop_camera_ip", methods=["POST"])
def stop_camera_ip():
    global camera
    if camera is not None and camera.isOpened():
        camera.release()
        camera = None
        return jsonify({"status": "success", "message": "Câmera IP parada com sucesso."})
    return jsonify({"status": "info", "message": "Nenhuma câmera IP ativa."})

def generate_frames():
    global camera
    if camera is None or not camera.isOpened():
        # Tenta abrir a câmera padrão se nenhuma IP estiver ativa
        camera = cv2.VideoCapture(0) 
        if not camera.isOpened():
            print("Erro: Nenhuma câmera (IP ou padrão) disponível.")
            return

    last_detection_time = time.time()

    while True:
        success, frame = camera.read()
        if not success:
            print("Erro ao ler frame da câmera.")
            break
        else:
            # Redimensionar o frame para um tamanho padrão para processamento
            frame = cv2.resize(frame, (640, 480))

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
                    current_time = time.time()
                    if current_time - last_detection_time > 10: # Simula ciclo a cada 10 segundos
                        last_detection_time = current_time

                    # Simula 'no meio' por 3 segundos
                    if current_time - last_detection_time < 3:
                        hand_proximity_status = "no meio"
                        detection_message = "Mão no meio do botão (simulado)!"
                    # Simula 'quase' por 3 segundos
                    elif current_time - last_detection_time < 6:
                        hand_proximity_status = "quase"
                        detection_message = "Mão quase pressionando o botão (simulado)!"
                    else:
                        hand_proximity_status = "longe"
                        detection_message = "Mão longe do botão (simulado)."

                    # Desenhar a caixa azul e o texto no frame
                    if button_bbox:
                        bx, by, bw, bh = button_bbox
                        cv2.rectangle(frame, (bx, by), (bx + bw, by + bh), (255, 0, 0), 3) # Azul

                        text_color = (0, 0, 255) # Vermelho
                        if hand_proximity_status == "no meio":
                            text_color = (0, 255, 0) # Verde
                        elif hand_proximity_status == "quase":
                            text_color = (0, 165, 255) # Laranja
                        
                        cv2.putText(frame, detection_message, (bx, by - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, text_color, 2)

            ret, buffer = cv2.imencode(".jpg", frame)
            frame = buffer.tobytes()
            yield (b"--frame\r\n"
                   b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")

@app.route("/video_feed")
def video_feed():
    return Response(generate_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

