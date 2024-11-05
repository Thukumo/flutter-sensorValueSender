import cv2
import numpy as np
import asyncio
import websockets
import time
from collections import deque

# WebSocketサーバーからのデータを格納する変数
accel_data = [0, 0, 0]
gyro_data = [0, 0, 0]

# カメラの初期化
cap = cv2.VideoCapture(0)

# VIOアルゴリズムの初期化
# ここにVIOアルゴリズムの初期化コードを追加します

async def websocket_handler(websocket, path):
    global accel_data, gyro_data
    async for message in websocket:
        if message.startswith("g"):
            accel_data = list(map(float, message.split(",")[1:]))
        elif message.startswith("r"):
            gyro_data = list(map(float, message.split(",")[1:]))

async def vio_algorithm():
    global accel_data, gyro_data
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # ここにVIOアルゴリズムの実装コードを追加します
        # accel_dataとgyro_dataを使用してVIOを実行します
        
        cv2.imshow('VIO', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        
        await asyncio.sleep(0.01)

async def main():
    server = await websockets.serve(websocket_handler, "0.0.0.0", 8765)
    await asyncio.gather(server.wait_closed(), vio_algorithm())

if __name__ == "__main__":
    asyncio.run(main())

cap.release()
cv2.destroyAllWindows()
