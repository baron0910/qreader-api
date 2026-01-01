# QReader API

🔍 **強大的 QR Code 辨識 API**，使用 YOLOv8 深度學習模型 + Pyzbar 解碼器。

專為**小型、模糊、傾斜**的困難 QR Code 設計，辨識率遠超傳統方案。

## 📊 辨識能力對比

| 方法 | 最大旋轉角度 |
|------|-------------|
| Pyzbar | 17° |
| OpenCV | 46° |
| **QReader (本服務)** | **79°** |

## 🚀 API 端點

### 健康檢查
```
GET /
```

### 解碼 QR Code
```
POST /decode
```

**支援格式：**
1. `multipart/form-data` - 上傳圖片檔案（field: `image` 或 `file`）
2. `application/json` - Base64 編碼 `{"image": "base64_string"}`
3. Raw binary - 直接傳送圖片二進位資料

**回應範例：**
```json
{
  "success": true,
  "data": "QR Code 內容",
  "count": 1,
  "processing_time_ms": 245.32
}
```

### 詳細解碼（含位置資訊）
```
POST /decode/detailed
```

**回應範例：**
```json
{
  "success": true,
  "results": [
    {
      "data": "QR Code 內容",
      "confidence": 0.95,
      "bbox": [100, 150, 300, 350]
    }
  ],
  "decoded_count": 1,
  "processing_time_ms": 268.15
}
```

## 🛠️ 部署到 Zeabur

1. Fork 此倉庫或直接連接到 Zeabur
2. 在 Zeabur 控制台選擇「從 GitHub 部署」
3. 選擇此倉庫
4. Zeabur 會自動偵測 Dockerfile 並部署

### 環境變數（可選）
| 變數名 | 預設值 | 說明 |
|--------|--------|------|
| PORT | 8080 | 服務端口 |

## 📝 在 n8n 中使用

### HTTP Request 節點設定

```
Method: POST
URL: https://你的zeabur網址/decode
Content Type: multipart/form-data
Body Parameters:
  - Name: file
  - Type: Binary Data
  - Input Data Field Name: data
```

### 解析回應（Code 節點）

```javascript
const response = $input.item.json;

if (response.success) {
  return {
    json: {
      activity_id: response.data,
      success: true
    }
  };
} else {
  return {
    json: {
      success: false,
      error: response.error
    }
  };
}
```

## 🔧 本地開發

```bash
# 安裝依賴
pip install -r requirements.txt

# 安裝 zbar（Linux）
sudo apt-get install libzbar0

# 啟動服務
python app.py
```

## 📦 技術棧

- **QReader**: YOLOv8 + Pyzbar 組合
- **Flask**: 輕量 Web 框架
- **Gunicorn**: 生產級 WSGI 伺服器
- **OpenCV**: 圖像處理

## 📄 License

MIT License
