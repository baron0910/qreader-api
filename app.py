from flask import Flask, request, jsonify
from flask_cors import CORS
from qreader import QReader
import cv2
import numpy as np
import base64
import os
import time

app = Flask(__name__)
CORS(app)  # 允許跨域請求

# 初始化 QReader（只在啟動時載入一次模型）
print("正在載入 QReader 模型...")
qreader = QReader(model_size='s', min_confidence=0.3)
print("QReader 模型載入完成！")


@app.route('/', methods=['GET'])
def health_check():
    """健康檢查端點"""
    return jsonify({
        'status': 'ok',
        'service': 'QReader API',
        'version': '1.0.0',
        'description': '強大的 QR Code 辨識 API，使用 YOLOv8 + Pyzbar'
    })


@app.route('/decode', methods=['POST'])
def decode_qr():
    """解碼 QR Code
    
    接受兩種格式：
    1. multipart/form-data: 上傳圖片檔案（field name: 'image' 或 'file'）
    2. application/json: Base64 編碼的圖片 {"image": "base64_string"}
    """
    start_time = time.time()
    
    try:
        img = None
        
        # 方式 1: 檢查是否有上傳檔案
        if 'image' in request.files:
            file = request.files['image']
            img_array = np.frombuffer(file.read(), np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        elif 'file' in request.files:
            file = request.files['file']
            img_array = np.frombuffer(file.read(), np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        
        # 方式 2: 檢查是否有 JSON body 包含 base64 圖片
        elif request.is_json:
            data = request.get_json()
            if 'image' in data:
                # 移除 data URL prefix（如果有的話）
                base64_str = data['image']
                if ',' in base64_str:
                    base64_str = base64_str.split(',')[1]
                
                img_bytes = base64.b64decode(base64_str)
                img_array = np.frombuffer(img_bytes, np.uint8)
                img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        
        # 方式 3: 檢查 raw binary data
        elif request.data:
            img_array = np.frombuffer(request.data, np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        
        if img is None:
            return jsonify({
                'success': False,
                'error': '無法讀取圖片，請確認格式正確',
                'accepted_formats': [
                    'multipart/form-data (field: image 或 file)',
                    'application/json {"image": "base64_string"}',
                    'raw binary image data'
                ]
            }), 400
        
        # 使用 QReader 解碼
        results = qreader.detect_and_decode(image=img)
        
        processing_time = time.time() - start_time
        
        # 過濾掉 None 結果
        decoded_data = [r for r in results if r is not None]
        
        if decoded_data:
            return jsonify({
                'success': True,
                'data': decoded_data[0] if len(decoded_data) == 1 else decoded_data,
                'count': len(decoded_data),
                'all_results': list(results),
                'processing_time_ms': round(processing_time * 1000, 2)
            })
        else:
            return jsonify({
                'success': False,
                'error': '未能識別 QR Code',
                'detected_count': len(results),
                'processing_time_ms': round(processing_time * 1000, 2)
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/decode/detailed', methods=['POST'])
def decode_qr_detailed():
    """解碼 QR Code 並返回詳細資訊（包含位置、信心度等）"""
    start_time = time.time()
    
    try:
        img = None
        
        if 'image' in request.files:
            file = request.files['image']
            img_array = np.frombuffer(file.read(), np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        elif 'file' in request.files:
            file = request.files['file']
            img_array = np.frombuffer(file.read(), np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        elif request.is_json:
            data = request.get_json()
            if 'image' in data:
                base64_str = data['image']
                if ',' in base64_str:
                    base64_str = base64_str.split(',')[1]
                img_bytes = base64.b64decode(base64_str)
                img_array = np.frombuffer(img_bytes, np.uint8)
                img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        elif request.data:
            img_array = np.frombuffer(request.data, np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        
        if img is None:
            return jsonify({
                'success': False,
                'error': '無法讀取圖片'
            }), 400
        
        # 使用 return_detections=True 獲取詳細資訊
        results = qreader.detect_and_decode(image=img, return_detections=True)
        
        processing_time = time.time() - start_time
        
        detailed_results = []
        for item in results:
            if isinstance(item, tuple) and len(item) == 2:
                decoded_text, detection = item
                detailed_results.append({
                    'data': decoded_text,
                    'confidence': float(detection.get('confidence', 0)) if detection else None,
                    'bbox': detection.get('bbox_xyxy', []).tolist() if detection and 'bbox_xyxy' in detection else None
                })
            else:
                detailed_results.append({
                    'data': item,
                    'confidence': None,
                    'bbox': None
                })
        
        successful = [r for r in detailed_results if r['data'] is not None]
        
        return jsonify({
            'success': len(successful) > 0,
            'results': detailed_results,
            'decoded_count': len(successful),
            'total_detected': len(detailed_results),
            'processing_time_ms': round(processing_time * 1000, 2)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
