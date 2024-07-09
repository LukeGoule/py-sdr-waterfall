import numpy as np
from matplotlib import pyplot as plt
from rtlsdr import RtlSdr

class SDRUtl(object):
    def __init__(self) -> None:
        self.sdr = RtlSdr()

    # Function to configure and read samples from the RTL-SDR
    def read_sdr_samples(self, frequency: int, gain: int, bandwidth: int = 2e6, sample_rate: int = 2.4e6, fft_size: int = 1024, num_rows: int = 500):
        # Configure device
        self.sdr.sample_rate = sample_rate
        self.sdr.center_freq = frequency
        self.sdr.gain = gain

        # Set the bandwidth if the SDR library supports it (some might not)
        try:
            self.sdr.set_bandwidth(bandwidth)
        except Exception as e:
            print(f"Warning: Bandwidth setting failed: {e}")

        # Read the required samples
        x = self.sdr.read_samples(fft_size * num_rows)

        return x

    # Converts a frequency string to an integer frequency
    def frequency_string_to_hz(self, freq_str: str) -> int:
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

def main():
    sdr = SDRUtl()

    # The frequency to start scanning from
    start_frequency = sdr.frequency_string_to_hz("70MHz")

    # The frequency to stop scanning at
    end_frequency = sdr.frequency_string_to_hz("130MHz")

    # The per-sample bandwidth
    bandwidth = 2e5

    # Total size of the output
    total_scan_bandwidth = end_frequency - start_frequency
    
    # The number of steps
    steps = int(total_scan_bandwidth / bandwidth)

    # FFT parameters
    sample_rate = 2.4e6
    fft_size = 4096

    # Initialize the power density array
    frequencies = np.linspace(start_frequency, end_frequency, steps)
    power_density = np.zeros(steps)

    for step in range(steps):
        frequency = start_frequency + step * bandwidth
        
        print( "Reading", str( ( frequency - ( bandwidth / 2 ) ) / 1e6 ) + "MHz to", str( ( frequency + ( bandwidth / 2 ) ) / 1e6 ) + "MHz" )
        
        samples = sdr.read_sdr_samples(
            frequency=frequency, 
            gain=1, 
            bandwidth=bandwidth, 
            sample_rate=sample_rate, 
            fft_size=fft_size, 
            num_rows=1
        )

        # Calculate FFT and power spectrum
        fft_result = np.fft.fftshift(np.fft.fft(samples, fft_size))
        power_spectrum = 20 * np.log10(np.abs(fft_result))

        # Averaging power density
        power_density[step] = np.mean(power_spectrum)

    # Convert frequencies to MHz for plotting
    frequencies_mhz = frequencies / 1e6

    # Plot the power spectrum
    plt.plot(frequencies_mhz, power_density)
    plt.xlabel("Frequency [MHz]")
    plt.ylabel("Power [dB]")
    plt.title("Power Spectrum")
    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    main()
