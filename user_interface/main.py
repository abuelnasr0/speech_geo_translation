import streamlit as st
import pandas as pd
import numpy as np
import requests
import io
import json
import soundfile as sf
from st_audiorec import st_audiorec

URL = "http://127.0.0.1:8000/upload/"

audio = st.file_uploader("Upload an audio file", type=["wav", "mp3"])
wav_audio_data = st_audiorec()

location = None

lang = st.radio(
    "Language",
    ["English", "Arabic"],
)

if st.button("GeoCode!"):
    if wav_audio_data is not None:

        # Check the type of wav_audio_data
        if isinstance(wav_audio_data, bytes):
            # Convert bytes to a NumPy array
            audio_array = np.frombuffer(wav_audio_data, dtype=np.int32)
        # Save the audio data to a WAV file using SoundFile
        wav_buffer = io.BytesIO()
        sf.write(
            wav_buffer, audio_array, 44100, format="wav"
        )  # Assuming a sample rate of 16 kHz

        # Seek to the beginning of the buffer for reading later
        wav_buffer.seek(0)

        files = {
            "file": wav_buffer,
        }
        # Send a POST request to upload the file
        print(lang)
        response = requests.post(URL, files=files, data={"lang": lang})

        print(response)
        # st.audio(wav_audio_data, format='audio/wav')

    elif audio is not None:
        print(lang)
        files = {
            "file": audio,
        }
        # Send a POST request to upload the file
        response = requests.post(URL, files=files, data={"lang": lang})

    if response.status_code == 200:
        response_data = response.json()
        print(response_data)
        if response_data["message"] != "Not Found":
            location = response_data["location"]

        for k in response_data.keys():
            st.header(k)
            if isinstance(response_data[k], dict):
                st.write(pd.DataFrame(response_data[k], index=[0]))
            else:
                st.text(response_data[k])
        print(response_data)


if location is not None:

    df = pd.DataFrame(
        np.array([[location["latitude"], location["longitude"]]]),
        columns=["lat", "lon"],
    )
    st.map(df, size=5)
