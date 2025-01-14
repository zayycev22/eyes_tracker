import asyncio
import uvicorn
from aiortc import RTCSessionDescription, RTCPeerConnection
from aiortc.contrib.media import MediaRelay, MediaBlackhole
from aiortc.rtcrtpreceiver import RemoteStreamTrack
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates
from contextlib import asynccontextmanager

from eyes_tracker import EyesTracker
from schemas import RTCModel

pcs = set()


@asynccontextmanager
async def on_shutdown(app: FastAPI):
    yield
    coros = [pc.close() for pc in pcs]
    await asyncio.gather(*coros)
    pcs.clear()


app = FastAPI(lifespan=on_shutdown)

origins = ['*']

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")


@app.get('/', response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request=request, name='index.html')


@app.post('/test_rtc')
async def rtc_test(data: RTCModel):
    offer = RTCSessionDescription(sdp=data.sdp, type=data.type)
    pc = RTCPeerConnection()
    pcs.add(pc)
    recorder = MediaBlackhole()
    relay = MediaRelay()

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        print("Connection state is %s" % pc.connectionState)
        if pc.connectionState == "failed":
            await pc.close()
            pcs.discard(pc)

    @pc.on("track")
    def on_track(track: RemoteStreamTrack):
        print(f"Получен трек: {track.kind}")
        if track.kind == "video":
            pc.addTrack(EyesTracker(relay.subscribe(track)))

            @track.on("ended")
            async def on_ended():
                await recorder.stop()

    await pc.setRemoteDescription(offer)
    await recorder.start()

    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)
    return {"sdp": answer.sdp, "type": answer.type}


if __name__ == '__main__':
    uvicorn.run(app)
