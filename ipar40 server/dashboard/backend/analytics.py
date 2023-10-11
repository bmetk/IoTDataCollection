import numpy as np
from scipy import signal
from scipy.fft import fft, fftfreq, fftshift
import json
#import ast

#import matplotlib.pyplot as plt

sampling_freq = 1000 # Hz

def string_to_array(arr_string: str):
    try:
        split_string = arr_string.strip("b'[]").split(',')
        vib_array = np.array([float(x.strip()) for x in split_string])
        return vib_array
    except json.JSONDecodeError:
        return None
    


def calculate_fft(vib_array : np.array([])) -> str:
    window = signal.windows.hamming(vib_array.size)
    windowed_data = vib_array * window

    fft_result = fft(windowed_data)
    freq = fftfreq(vib_array.size, d=1.0/sampling_freq)
    positive_freq = freq[:len(freq) // 2]
    fft_result_positive = 2.0 / vib_array.size * np.abs(fft_result[:len(fft_result) // 2])

    # Filter the FFT result to avoid aliasing based on the Nyquist frequency
    nyquist_freq = sampling_freq / 2
    fft_filtered = fft_result_positive[freq[:len(fft_result) // 2] <= nyquist_freq]

    return str(fft_filtered.tolist())

# calculates the Root Mean Square of the vibration data
def calculate_rms(vib_array : np.array) -> float:
    return str(np.sqrt(np.mean(vib_array**2)))

# calculates the power spectral density of the vibration data
def get_psd(vib_array : np.array) -> str:
    f, Pxx_den = signal.periodogram(vib_array, fs=sampling_freq, window='hamming')
    return str([f.tolist(), Pxx_den.tolist()])
