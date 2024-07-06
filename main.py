import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from rtlsdr import RtlSdr
from tkinter import Tk, Label, Entry, Button

class RTLSDRInterface:
    def __init__(self, master):
        self.master = master
        self.master.title("RTL-SDR Interface")

        # Frequency input
        Label(master, text="Center Frequency (Hz):").grid(row=0, column=0)
        self.freq_entry = Entry(master)
        self.freq_entry.grid(row=0, column=1)
        self.freq_entry.insert(0, "100.3Mhz")
        self.frequency = None

        # Sample rate input
        Label(master, text="Sample Rate (Hz):").grid(row=1, column=0)
        self.sample_rate_entry = Entry(master)
        self.sample_rate_entry.grid(row=1, column=1)
        self.sample_rate_entry.insert(0, "2.048MHz")
        self.sample_rate = None

        # Gain input
        Label(master, text="Gain:").grid(row=2, column=0)
        self.gain_entry = Entry(master)
        self.gain_entry.grid(row=2, column=1)
        self.gain_entry.insert(0, "auto")
        self.gain = None

        # Rows input
        Label(master, text="Rows:").grid(row=3, column=0)
        self.rows_entry = Entry(master)
        self.rows_entry.grid(row=3, column=1)
        self.rows_entry.insert(0, "1")
        self.rows = None

        # Start button
        self.start_button = Button(master, text="Start", command=self.start)
        self.start_button.grid(row=4, column=0, columnspan=1)

        self.update_button = Button(master, text="Update", command=self.update)
        self.update_button.grid(row=4, column=1, columnspan=1)

        # Create figure for spectrogram
        self.fig, self.ax = plt.subplots()
        self.sdr = None
        self.ani = None

        # Spectrogram parameters
        self.buffer_size = 100  # Number of time bins in the waterfall display
        self.freq_bins = 2048    # Number of frequency bins
        self.spectrogram_buffer = np.zeros((self.buffer_size, self.freq_bins))

    def frequency_string_to_hz(self, freq_str : str) -> int:
        # Define the units and their corresponding multipliers
        units = {
            'khz': 1e3,
            'mhz': 1e6,
            'ghz': 1e9
        }
        
        # Parse the input string to extract the numerical value and the unit
        for unit in units:
            if freq_str.lower().endswith(unit):
                value = float(freq_str[:-len(unit)])
                return int(value * units[unit])
        
        # Raise an error if the unit is not recognized
        raise ValueError(f"Unrecognized frequency unit in '{freq_str}'")

    def start(self):
        if self.sdr is None:
            self.sdr = RtlSdr()
            self.sample_rate = self.sdr.sample_rate = self.frequency_string_to_hz(self.sample_rate_entry.get())
            self.frequency = self.sdr.center_freq = self.frequency_string_to_hz(self.freq_entry.get())
            self.rows = self.rows_entry.get()
            gain = self.gain_entry.get()
            if gain.lower() == "auto":
                self.gain = self.sdr.gain = "auto"
            else:
                self.gain = self.sdr.gain = float(gain)

        if self.ani is not None:
            self.ani.event_source.stop()

        self.ani = animation.FuncAnimation(self.fig, self.update_spectrogram, interval=int(1000 / 60), cache_frame_data=False)
        plt.show()

    def update(self):
        self.sample_rate = self.sdr.sample_rate = self.frequency_string_to_hz(self.sample_rate_entry.get())
        self.frequency = self.sdr.center_freq = self.frequency_string_to_hz(self.freq_entry.get())
        self.rows = self.rows_entry.get()
        self.gain = self.gain_entry.get()

        if self.gain.lower() == "auto":
            self.sdr.gain = "auto"
        else:
            self.sdr.gain = float(self.gain)

    def update_spectrogram(self, frame):
        fft_size = 2048

        # Apply a Hamming window to reduce spectral leakage
        window = np.hamming(fft_size)

        samples = self.sdr.read_samples(int(self.rows)*fft_size)
        Pxx, freqs, bins = plt.mlab.specgram(samples, NFFT=fft_size, Fs=self.sdr.sample_rate, noverlap=512)

        # Update the buffer
        self.spectrogram_buffer = np.roll(self.spectrogram_buffer, -1, axis=0)
        
        for i in range(int(self.rows)):
            segment = samples[i * fft_size:(i + 1) * fft_size] * window
            spectrum = np.fft.fftshift(np.fft.fft(segment))
            self.spectrogram_buffer[-1, :] = np.log10(np.abs(spectrum)**2)

        extent = [(self.frequency - self.sample_rate / 2) / 1e6,
              (self.frequency + self.sample_rate / 2) / 1e6,
              int(self.rows) / self.sample_rate, 0]

        self.ax.clear()
        self.ax.imshow(self.spectrogram_buffer, aspect='auto', extent=extent)
        self.ax.set_title('Waterfall Spectrogram')
        self.ax.set_xlabel('Frequency (Hz)')
        self.ax.set_ylabel('Time (s)')

root = Tk()
app = RTLSDRInterface(root)
root.mainloop()
