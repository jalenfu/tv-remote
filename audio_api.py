from fastapi import APIRouter, Body, Query
from fastapi.responses import JSONResponse
from pycaw.constants import EDataFlow, DEVICE_STATE
from pycaw.pycaw import AudioUtilities
from pycaw.utils import AudioDevice
import warnings
import comtypes
eRender = 0  # eRender = 0 for playback devices

audio_router = APIRouter()

@audio_router.get('/api/audio/devices')
def get_audio_devices():
    comtypes.CoInitialize()
    with warnings.catch_warnings():  # suppress COMError warnings
        warnings.simplefilter("ignore", UserWarning)
        devices = AudioUtilities.GetAllDevices(data_flow=EDataFlow.eRender.value,
                                            device_state=DEVICE_STATE.ACTIVE.value)
        device_ret = []
        for device in devices:
            device_ret.append({'id': device.id, 'name': device.FriendlyName})
        comtypes.CoUninitialize()
        return {'devices': device_ret}


@audio_router.post('/api/audio/device')
def set_audio_device(device_id: str = Body(..., embed=True)):
    comtypes.CoInitialize()
    try:
        AudioUtilities.SetDefaultDevice(device_id)
        comtypes.CoUninitialize()
        return {'status': f'Set playback device to {device_id}'}
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500) 
    
@audio_router.get('/api/audio/currentdevice')
def get_current_device():
    comtypes.CoInitialize()
    try:
        device = AudioUtilities.GetSpeakers()
        comtypes.CoUninitialize()
        return {'device': {'id': device.id, 'name': device.FriendlyName}}
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500) 

from pycaw.pycaw import IAudioEndpointVolume

@audio_router.get('/api/audio/system_volume')
def get_system_volume():
    try:
        comtypes.CoInitialize()
        device = AudioUtilities.GetSpeakers()
        volume = device.EndpointVolume
        volume = comtypes.cast(volume, comtypes.POINTER(IAudioEndpointVolume))
        level = volume.GetMasterVolumeLevelScalar()
        comtypes.CoUninitialize()
        return {"volume": level}
    except Exception as e:
        comtypes.CoUninitialize()
        return JSONResponse({"error": f"Failed to get system volume: {e}"}, status_code=500)

@audio_router.post('/api/audio/system_volume')
def set_system_volume(level: float = Query(..., ge=0.0, le=1.0)):
    try:
        comtypes.CoInitialize()
        device = AudioUtilities.GetSpeakers()
        volume = device.EndpointVolume
        volume = comtypes.cast(volume, comtypes.POINTER(IAudioEndpointVolume))
        volume.SetMasterVolumeLevelScalar(level, None)
        comtypes.CoUninitialize()
        return {"status": f"System volume set to {level:.2f}"}
    except Exception as e:
        comtypes.CoUninitialize()
        return JSONResponse({"error": f"Failed to set system volume: {e}"}, status_code=500) 