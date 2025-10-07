from flask import Flask, request, jsonify, Response
import whisper
import tempfile
import os
import json
import time

app = Flask(__name__)
MODEL_SIZE = os.environ.get("MODEL_SIZE", "tiny")
PORT = int(os.environ.get("PORT", "5005"))

print(f"🚀 Iniciando Whisper API...")
print(f"📦 Carregando modelo Whisper (size={MODEL_SIZE})...")
start_time = time.time()
model = whisper.load_model(MODEL_SIZE)
load_time = time.time() - start_time
print(f"✅ Modelo carregado em {load_time:.2f}s")

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint para Railway"""
    return jsonify({
        "status": "healthy",
        "model": MODEL_SIZE,
        "port": PORT
    }), 200

@app.route('/', methods=['GET'])
def index():
    """Endpoint raiz com informações do serviço"""
    return jsonify({
        "service": "Whisper Transcription API",
        "model": MODEL_SIZE,
        "version": "1.0",
        "endpoints": {
            "transcribe": "POST /transcribe (multipart/form-data com campo 'file')",
            "health": "GET /health"
        }
    }), 200

@app.route('/transcribe', methods=['POST'])
def transcribe_audio():
    """Endpoint principal de transcrição"""
    if 'file' not in request.files:
        return jsonify({
            "error": "Arquivo de áudio não enviado. Use campo 'file'.",
            "usage": "POST /transcribe com multipart/form-data"
        }), 400

    audio_file = request.files['file']
    
    if audio_file.filename == '':
        return jsonify({"error": "Nome de arquivo vazio"}), 400
    
    # Salvar temporariamente
    suffix = os.path.splitext(audio_file.filename)[1] or ".ogg"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        audio_path = tmp.name
        audio_file.save(audio_path)

    try:
        print(f"🎤 Transcrevendo: {audio_file.filename}")
        start = time.time()
        
        # Transcrever com configurações otimizadas
        result = model.transcribe(
            audio_path, 
            language="pt",
            fp16=False  # CPU não suporta fp16
        )
        
        text = result.get("text", "").strip()
        duration = time.time() - start
        
        # Remover arquivo temporário
        os.remove(audio_path)
        
        print(f"✅ Transcrito em {duration:.2f}s")
        
        # Retornar resposta com encoding UTF-8 correto
        payload = json.dumps({
            "text": text,
            "language": result.get("language", "pt"),
            "duration": round(duration, 2)
        }, ensure_ascii=False)
        
        return Response(payload, mimetype="application/json; charset=utf-8")

    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        try:
            os.remove(audio_path)
        except:
            pass
        return jsonify({
            "error": str(e),
            "file": audio_file.filename
        }), 500

if __name__ == '__main__':
    print(f"🌐 Servidor iniciando na porta {PORT}")
    app.run(host="0.0.0.0", port=PORT, debug=False)
