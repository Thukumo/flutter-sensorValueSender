import asyncio
import websockets

async def receive_messages(websocket):
    async for message in websocket:
        print(f"Received message: {message}")

async def perform_other_task():
    while True:
        print("Performing other task...")
        await asyncio.sleep(1)  # 1秒ごとにタスクを実行

async def main():
    uri = "ws://your_websocket_server_address"
    async with websockets.connect(uri) as websocket:
        # WebSocketでメッセージを受け取るタスクを作成
        receive_task = asyncio.create_task(receive_messages(websocket))
        # 別のタスクを実行するタスクを作成
        other_task = asyncio.create_task(perform_other_task())
        
        # 両方のタスクを並行して実行
        await asyncio.gather(receive_task, other_task)

if __name__ == "__main__":
    asyncio.run(main())
