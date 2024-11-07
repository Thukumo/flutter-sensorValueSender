import scipy.constants
import asyncio, websockets, time, scipy
import math

rotatelis = [0, 0, 0]
filtered_l = [0, 0, 0]
gyro_data = [0, 0, 0]  # ジャイロスコープデータ
last_gyro_time = time.time()  # ジャイロデータの時間管理用
previous_l = [0, 0, 0]  # 前回の加速度値を保存
yaw = 0  # 累積ヨー角
alpha = 0.05  # より強いノイズ除���のため小さい値に調整
noise_threshold = 0.01  # ノイズ閾値
calibration_samples = []  # キャリブレーション用のサンプル
calibration_offset = [0, 0, 0]  # キャリブレーション時のオフセット
is_calibrated = False
connected = False

CALIBRATION_SAMPLES = 50  # キャリブレーションに必要なサンプル数
EXPECTED_GRAVITY = scipy.constants.g    # 期待される重力加速度値

send_uri = "ws://別のデバイスのIPアドレス:ポート"  # 送信先のWebSocket URI

# send_uri と send_websocket の代わりに接続クライアント管理用の変数を追加
connected_clients = set()

def apply_calibration(values):
    return [values[i] - calibration_offset[i] for i in range(3)]

def calibrate(samples):
    if len(samples) < CALIBRATION_SAMPLES:
        return False
        
    global calibration_offset
    # 平均値を計算
    avg_values = [
        sum(sample[i] for sample in samples) / len(samples)
        for i in range(3)
    ]
    
    # キャリブレーションの品質チェック
    magnitude = math.sqrt(sum(x*x for x in avg_values))
    if abs(magnitude - EXPECTED_GRAVITY) > 0.1:  # 重力加速度との差が大きすぎる場合
        print(f"Warning: デバイスが水平でない可能性があります: {magnitude:.3f}")
        return False
        
    calibration_offset = avg_values
    calibration_offset[2] -= EXPECTED_GRAVITY  # Z軸は重力加速度を考慮
    
    print(f"オフセッ���値: X={calibration_offset[0]:.3f}, Y={calibration_offset[1]:.3f}, Z={calibration_offset[2]:.3f}")
    return True

async def broadcast_angles():
    while True:
        if connected:
            # 接続が切れたクライアントを除去
            disconnected = set()
            for client in connected_clients:
                try:
                    await client.send(f"angles,{rotatelis[0]:.5f},{rotatelis[1]:.5f},{rotatelis[2]:.5f}")
                except websockets.exceptions.ConnectionClosed:
                    disconnected.add(client)
            connected_clients.difference_update(disconnected)
        await asyncio.sleep(0.1)

async def handler(websocket, path):
    global rotatelis, filtered_l, connected, calibration_samples, is_calibrated, gyro_data, last_gyro_time, previous_l, yaw
    normalized_l = [0, 0, 0]  # normalized_l の初期化を追加
    try:
        if path == "/data":  # データを受信するパス
            print("キャリブレーション開始: デバイスを水平に置いて静止させてください")
            async for message in websocket:
                connected = True
                if message.startswith("a"):
                    l = list(map(float, message.split(",")[1:]))
                    
                    # キャリブレーション処理
                    if not is_calibrated:
                        calibration_samples.append(l)
                        print(f"キャリブレーション中: {len(calibration_samples)}/{CALIBRATION_SAMPLES}")
                        if len(calibration_samples) >= CALIBRATION_SAMPLES:
                            is_calibrated = calibrate(calibration_samples)
                            if is_calibrated:
                                print("キャリブレーション完了")
                            else:
                                print("キャリブレーション失敗: やり直してください")
                                calibration_samples = []
                        continue

                    # キャリブレーション適用
                    l = apply_calibration(l)
                    
                    # ノイズフィルタ処理
                    for i in range(3):
                        # 微小な変化は無視
                        if abs(l[i] - filtered_l[i]) < noise_threshold:
                            l[i] = filtered_l[i]
                        # ローパスフィルタ適用
                        filtered_l[i] = alpha * l[i] + (1 - alpha) * filtered_l[i]
                    
                    # 重力加速度で正規化
                    magnitude = math.sqrt(sum(x*x for x in filtered_l))
                    if magnitude != 0:
                        normalized_l = [x/magnitude for x in filtered_l]
                    else:
                        normalized_l = filtered_l

                    # 角度計算
                    pitch = math.atan2(-normalized_l[0], 
                        math.sqrt(normalized_l[1]**2 + normalized_l[2]**2))
                    roll = math.atan2(normalized_l[1], normalized_l[2])
                    
                    # 加速度センサーの値は補助的に使用
                    target_yaw = yaw
                    
                elif message.startswith("r"):
                    # ジャイロスコープデータの処理
                    gyro_values = list(map(float, message.split(",")[1:]))
                    current_time = time.time()
                    dt = current_time - last_gyro_time
                    last_gyro_time = current_time
                    
                    # Z軸の回転速度からヨー角を計算（度数法）
                    yaw += gyro_values[2] * dt
                    # ヨー角を-180から180の範囲に正規化
                    yaw = ((yaw + 180) % 360) - 180
                    
                    # 最終的な角度を更新
                    rotatelis = [
                        math.degrees(pitch) if 'pitch' in locals() else rotatelis[0],
                        math.degrees(roll) if 'roll' in locals() else rotatelis[1],
                        yaw
                    ]
                    
                    # ヨー角の変化を推定（normalized_l が更新されている場合のみ）
                    if previous_l != [0, 0, 0] and any(normalized_l):
                        delta_yaw = math.atan2(
                            normalized_l[1] * previous_l[0] - normalized_l[0] * previous_l[1],
                            normalized_l[0] * previous_l[0] + normalized_l[1] * previous_l[1]
                        )
                        yaw += math.degrees(delta_yaw) * 0.1  # 感度調整係数
                        
                        # ヨー角を-180から180の範囲に正規化
                        yaw = ((yaw + 180) % 360) - 180
                    
                    previous_l = normalized_l.copy() if any(normalized_l) else previous_l
                    
                    # 角度を度数法に変換
                    rotatelis = [
                        math.degrees(pitch) if 'pitch' in locals() else rotatelis[0],
                        math.degrees(roll) if 'roll' in locals() else rotatelis[1],
                        yaw  # 推定されるヨー角
                    ]
                
        elif path == "/angles":  # 角度データを受信するクライアント用のパス
            connected_clients.add(websocket)
            print(f"新しいクライアントが接続しました。現在の接続数: {len(connected_clients)}")
            try:
                await websocket.wait_closed()
            finally:
                connected_clients.remove(websocket)
                print(f"クライアントが切断しました。現在の接続数: {len(connected_clients)}")
    except websockets.exceptions.ConnectionClosedError:
        pass
    finally:
        if path == "/data":
            connected = False

async def print_eachlist():
    while True:
        if connected: print(f"rotatelis: {', '.join(f'{s:>.5f}'.zfill(9) for s in rotatelis)}")
        await asyncio.sleep(0.5)

async def main():
    await websockets.serve(handler, "0.0.0.0", 8765)
    asyncio.create_task(print_eachlist())
    asyncio.create_task(broadcast_angles())  # broadcast用タスクを追加
    await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
