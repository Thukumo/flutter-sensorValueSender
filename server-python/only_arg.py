import asyncio, websockets, time

srotatelis = [0, 0, 0]
rotatelis = [0, 0, 0]
ltr = 0

async def handler(websocket, path):
    global rotatelis, ltr, srotatelis
    async for message in websocket:
        if message.startswith("r"):
            old = ltr
            ltr = time.perf_counter()
            if old == 0: continue
            l = list(map(lambda x: float(x)*(ltr-old), message.split(",")[1:]))
            #print(f"l: {l}")
            oldsrotatelis = srotatelis[:]
            srotatelis = [srotatelis[i]+l[i] for i in range(3)]
            rotatelis = [(srotatelis[i] + oldsrotatelis[i])*(ltr-old)/2 for i in range(3)]

async def print_eachlist():
    global rotatelis
    while True:
        print(f"rotatelis: {rotatelis}")
        await asyncio.sleep(0.01)

async def main():
    await websockets.serve(handler, "0.0.0.0", 8765)
    asyncio.create_task(print_eachlist())
    await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
