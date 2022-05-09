import alsaaudio
from websocket import create_connection
import json
import time
import sys

# Relationship between camillaDSP and alsa volumes: ALSAvol = CDSPvol + 100
# values are converted to ALSA format instead of CDSP
# Get volume levels
def get_cdsp_vol(ws):
    ws.send(json.dumps("GetVolume"))
    reply = json.loads(ws.recv())
    return int(reply["GetVolume"]["value"] + 100)

def get_alsa_vol(mixer):
    try:
        mixer = alsaaudio.Mixer('PCM')
        vol = mixer.getvolume(alsaaudio.PCM_CAPTURE)
        return vol[0]
    except alsaaudio.ALSAAudioError:
        print("Error trying to get ALSA volume")
        pass

# Set volume levels
def set_cdsp_vol(ws, vol):
    vol = vol - 100
    ws.send(json.dumps({"SetVolume": vol}))
    print(ws.recv())

def set_alsa_vol(mixer, vol):
    try:
        mixer.setvolume(vol)
    except alsaaudio.ALSAAudioError:
        print("Error trying to set ALSA volume")
        pass

# Get mute values
def get_cdsp_mute(ws):
    ws.send(json.dumps("GetMute"))
    reply = json.loads(ws.recv())
    bool = reply["GetMute"]["value"]
    if bool == False:
        return 1
    else:
        return 0

def get_alsa_mute(mixer):
    try:
        mixer = alsaaudio.Mixer('PCM') # this is a fix for bug in one of the libraries. Have to remake the object to detect a change for getrec()
        mute = mixer.getrec()
        return mute[0]
    except alsaaudio.ALSAAudioError:
        print("Error getting ALSA mute")
        pass

# Set mute values
def set_cdsp_mute(ws, mute):
    if mute == 1:
        mute = False
    else:
        mute = True
    ws.send(json.dumps({"SetMute": mute}))
    print(ws.recv())

def set_alsa_mute(mixer, mute):
    try:
        mixer.setrec(mute)
    except alsaaudio.ALSAAudioError:
        print("Error setting ALSA mute")
        pass

# ---------- main ------------


# Create connection got camillaDSP websocket
# if you changed the -p option to another port number, change the "1234" port below
cdsp_ws = create_connection("ws://127.0.0.1:1234")

# Create alsaaudio mixer from PCM mixer
try:
    pcm_mixer = alsaaudio.Mixer('PCM')
    print("Mixer 'PCM' added")
except alsaaudio.ALSAAudioError:
    print("PCM Mixer not found!")
    sys.exit(1)


CDSPvol = get_cdsp_vol(cdsp_ws)
ALSAvol = get_alsa_vol(pcm_mixer)
CDSPmute = get_cdsp_mute(cdsp_ws)
ALSAmute = get_alsa_mute(pcm_mixer)

print("Starting values:")
print("CDSPvol = " + str(CDSPvol) + " | CDSPmute = " + str(CDSPmute) + " | ALSAvol = " + str(ALSAvol) + " | ALSAmute = " + str(ALSAmute))


# Set ALSA values to those of CDSP at startup
set_alsa_vol(pcm_mixer, CDSPvol)
set_alsa_mute(pcm_mixer, CDSPvol)

while(True):
    # get current values
    ALSAvol = get_alsa_vol(pcm_mixer)
    CDSPvol = get_cdsp_vol(cdsp_ws)

    ALSAmute = get_alsa_mute(pcm_mixer)
    CDSPmute = get_cdsp_mute(cdsp_ws)

    # Volume was changed from the host computer
    if CDSPvol != ALSAvol:
        set_cdsp_vol(cdsp_ws, ALSAvol)
        print("Volume Changed:")
        print("CDSPvol = " + str(CDSPvol) + " | CDSPmute = " + str(CDSPmute) + " | ALSAvol = " + str(ALSAvol) + " | ALSAmute = " + str(ALSAmute))

    # Mute was changed from the host computer
    if CDSPmute != ALSAmute:
        set_cdsp_mute(cdsp_ws, ALSAmute)
        CDSPmute = get_cdsp_mute(cdsp_ws)
        print("Mute Changed")
        print("CDSPvol = " + str(CDSPvol) + " | CDSPmute = " + str(CDSPmute) + " | ALSAvol = " + str(ALSAvol) + " | ALSAmute = " + str(ALSAmute))

    # Wait a little bit to avoid excessive CPU overhead
    time.sleep(0.25)
