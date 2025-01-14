from pydantic import BaseModel


class RTCModel(BaseModel):
    sdp: str
    type: str
