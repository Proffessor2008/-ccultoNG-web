import base64
import hashlib
import io
import struct
import wave
from typing import List

import numpy as np
from PIL import Image


class StegoException(Exception):
    """Custom exception for steganography operations"""
    pass


class LSBImageSteganography:
    """LSB (Least Significant Bit) steganography for images"""

    def __init__(self):
        self.HEADER_SIZE = 128  # Increased for filename storage
        self.MAGIC_BYTES = b'STGO'  # Magic bytes for identification

    def hide_data(self, image_data: bytes, secret_data: bytes, password: str = "",
                  original_filename: str = "") -> bytes:
        """
        Hide secret data in image using LSB method

        Args:
            image_data: Raw image data
            secret_data: Data to hide
            password: Optional password for encryption
            original_filename: Original filename to preserve

        Returns:
            Modified image data with hidden information
        """
        try:
            # Load image
            image = Image.open(io.BytesIO(image_data))

            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')

            # Get pixel data
            pixels = np.array(image)
            flat_pixels = pixels.flatten()

            # Prepare data with header
            data_with_header = self._prepare_data(secret_data, password, original_filename)

            # Check capacity
            available_bits = len(flat_pixels) * 3  # 3 channels per pixel
            required_bits = len(data_with_header) * 8 + self.HEADER_SIZE

            if required_bits > available_bits:
                raise StegoException("Image too small to hide data")

            # Hide data using LSB
            stego_pixels = self._hide_bits(flat_pixels, data_with_header)

            # Reshape back to image dimensions
            stego_image = stego_pixels.reshape(pixels.shape)

            # Save as PNG to avoid compression artifacts
            output = io.BytesIO()
            Image.fromarray(stego_image.astype(np.uint8)).save(output, format='PNG')

            return output.getvalue()

        except Exception as e:
            raise StegoException(f"Failed to hide data: {str(e)}")

    def extract_data(self, stego_image_data: bytes, password: str = "") -> tuple:
        """
        Extract hidden data from stego image

        Args:
            stego_image_data: Image with hidden data
            password: Password for decryption

        Returns:
            Tuple of (extracted_data, original_filename)
        """
        try:
            # Load image
            image = Image.open(io.BytesIO(stego_image_data))

            if image.mode != 'RGB':
                image = image.convert('RGB')

            # Get pixel data
            pixels = np.array(image)
            flat_pixels = pixels.flatten()

            # Extract header first
            header_bits = self._extract_bits(flat_pixels, self.HEADER_SIZE)
            header_bytes = self._bits_to_bytes(header_bits)

            # Verify magic bytes
            if header_bytes[:4] != self.MAGIC_BYTES:
                raise StegoException("No hidden data found or invalid format")

            # Extract data size and filename
            data_size = struct.unpack('>I', header_bytes[4:8])[0]

            # Extract filename length and filename
            filename_length = struct.unpack('>H', header_bytes[8:10])[0]
            original_filename = ""
            if filename_length > 0:
                original_filename = header_bytes[10:10 + filename_length].decode('utf-8', errors='ignore')

            # Extract actual data
            total_bits = self.HEADER_SIZE + (data_size * 8)
            all_bits = self._extract_bits(flat_pixels, total_bits)
            data_bits = all_bits[self.HEADER_SIZE:]

            # Convert to bytes - ensure we get exactly data_size bytes
            extracted_data = self._bits_to_bytes(data_bits)
            extracted_data = extracted_data[:data_size]  # Truncate to exact size

            # Verify integrity
            stored_hash_start = 10 + filename_length
            stored_hash = header_bytes[stored_hash_start:stored_hash_start + 32]  # 32 bytes for SHA256
            calculated_hash = hashlib.sha256(extracted_data).digest()

            if stored_hash != calculated_hash:
                print(
                    f"WARNING: Hash mismatch - stored: {stored_hash.hex()[:16]}..., calculated: {calculated_hash.hex()[:16]}...")

            return extracted_data, original_filename

        except Exception as e:
            raise StegoException(f"Failed to extract data: {str(e)}")

    def _prepare_data(self, secret_data: bytes, password: str, original_filename: str) -> bytes:
        """Prepare data with header and integrity check"""
        # Calculate data hash
        data_hash = hashlib.sha256(secret_data).digest()

        # Prepare filename
        filename_bytes = original_filename.encode('utf-8') if original_filename else b''
        filename_length = len(filename_bytes)

        # Create header with filename support
        data_size = len(secret_data)
        header = (self.MAGIC_BYTES +
                  struct.pack('>I', data_size) +
                  struct.pack('>H', filename_length) +
                  filename_bytes +
                  data_hash)

        # Pad header to fixed size
        header = header.ljust(self.HEADER_SIZE // 8, b'\x00')

        return header + secret_data

    def _hide_bits(self, pixels: np.ndarray, data: bytes) -> np.ndarray:
        """Hide data bits in LSB of pixels"""
        stego_pixels = pixels.copy()
        data_bits = self._bytes_to_bits(data)

        bit_index = 0
        for i in range(len(stego_pixels)):
            if bit_index < len(data_bits):
                # Clear LSB and set new bit
                stego_pixels[i] = (stego_pixels[i] & 0xFE) | data_bits[bit_index]
                bit_index += 1
            else:
                break

        return stego_pixels

    def _extract_bits(self, pixels: np.ndarray, num_bits: int) -> List[int]:
        """Extract bits from LSB of pixels"""
        bits = []
        for i in range(min(num_bits, len(pixels))):
            bits.append(pixels[i] & 1)
        return bits

    def _bytes_to_bits(self, data: bytes) -> List[int]:
        """Convert bytes to list of bits"""
        bits = []
        for byte in data:
            for i in range(8):
                bits.append((byte >> (7 - i)) & 1)
        return bits

    def _bits_to_bytes(self, bits: List[int]) -> bytes:
        """Convert list of bits to bytes"""
        bytes_data = bytearray()
        for i in range(0, len(bits), 8):
            byte = 0
            for j in range(min(8, len(bits) - i)):
                byte = (byte << 1) | bits[i + j]
            bytes_data.append(byte)
        return bytes(bytes_data)


class LSBAudioSteganography:
    """LSB steganography for WAV audio files with stereo support"""

    def __init__(self):
        self.HEADER_SIZE = 128  # Increased for filename storage
        self.MAGIC_BYTES = b'STGA'  # Magic bytes for audio

    def hide_data(self, audio_data: bytes, secret_data: bytes, password: str = "",
                  original_filename: str = "") -> bytes:
        """
        Hide secret data in WAV audio file using LSB with stereo support
        """
        try:
            # Parse WAV file
            with wave.open(io.BytesIO(audio_data), 'rb') as wav_file:
                params = wav_file.getparams()
                frames = wav_file.readframes(wav_file.getnframes())

            # Convert to byte array for manipulation
            frames_array = bytearray(frames)

            # Prepare data with header
            data_with_header = self._prepare_data(secret_data, password, original_filename)

            # Convert data to bits
            data_bits = self._bytes_to_bits(data_with_header)

            # Calculate available capacity considering stereo
            available_bits = self._calculate_audio_capacity(frames_array, params)
            required_bits = len(data_bits)

            if required_bits > available_bits:
                raise StegoException("Audio file too small to hide data")

            # Hide data in LSB with stereo consideration
            self._hide_audio_bits(frames_array, data_bits, params)

            # Create new WAV file
            output = io.BytesIO()
            with wave.open(output, 'wb') as wav_file:
                wav_file.setparams(params)
                wav_file.writeframes(bytes(frames_array))

            return output.getvalue()

        except Exception as e:
            raise StegoException(f"Failed to hide data in audio: {str(e)}")

    def extract_data(self, stego_audio_data: bytes, password: str = "") -> tuple:
        """
        Extract hidden data from stego audio file with stereo support
        """
        try:
            # Parse WAV file
            with wave.open(io.BytesIO(stego_audio_data), 'rb') as wav_file:
                params = wav_file.getparams()
                frames = wav_file.readframes(wav_file.getnframes())

            # Convert to byte array for extraction
            frames_array = bytearray(frames)

            # Extract header bits
            header_bits_len = self.HEADER_SIZE
            if len(frames_array) < header_bits_len:
                raise StegoException("Недостаточно данных для заголовка.")

            header_bits = self._extract_audio_bits(frames_array, header_bits_len, params)
            header_bytes = self._bits_to_bytes(header_bits)

            # Verify magic bytes
            if header_bytes[:4] != self.MAGIC_BYTES:
                raise StegoException("No hidden audio data found or invalid format")

            # Extract data size and filename
            data_size = struct.unpack('>I', header_bytes[4:8])[0]

            # Extract filename length and filename
            filename_length = struct.unpack('>H', header_bytes[8:10])[0]
            original_filename = ""
            if filename_length > 0:
                original_filename = header_bytes[10:10 + filename_length].decode('utf-8', errors='ignore')

            # Calculate total bits needed
            total_bits_needed = header_bits_len + (data_size * 8)

            # Extract all bits
            all_bits = self._extract_audio_bits(frames_array, total_bits_needed, params)

            # Get only data bits (skip header)
            data_bits = all_bits[header_bits_len:]

            # Convert bits to bytes
            extracted_data = self._bits_to_bytes(data_bits)
            extracted_data = extracted_data[:data_size]  # Truncate to exact size

            # Verify integrity
            stored_hash_start = 10 + filename_length
            stored_hash = header_bytes[stored_hash_start:stored_hash_start + 32]
            calculated_hash = hashlib.sha256(extracted_data).digest()

            if stored_hash != calculated_hash:
                print(
                    f"WARNING: Hash mismatch - stored: {stored_hash.hex()[:16]}..., calculated: {calculated_hash.hex()[:16]}...")

            return extracted_data, original_filename

        except Exception as e:
            raise StegoException(f"Failed to extract audio data: {str(e)}")

    def _calculate_audio_capacity(self, frames_array: bytearray, params) -> int:
        """Calculate available bits considering stereo configuration"""
        nchannels = params.nchannels
        sampwidth = params.sampwidth

        if nchannels == 1:
            # Mono: use all bytes
            return len(frames_array)
        elif nchannels == 2:
            # Stereo: use only left channel to minimize distortion
            # For 16-bit stereo, use every 4th byte (left channel low byte)
            if sampwidth == 2:
                return len(frames_array) // 4
            else:
                # For 8-bit stereo, use every 2nd byte
                return len(frames_array) // 2
        else:
            # Multi-channel: use only first channel
            return len(frames_array) // nchannels

    def _hide_audio_bits(self, frames_array: bytearray, data_bits: list, params):
        """Hide bits in audio data considering stereo configuration"""
        nchannels = params.nchannels
        sampwidth = params.sampwidth

        bit_index = 0
        data_length = len(data_bits)

        if nchannels == 1:
            # Mono: use all bytes
            for i in range(len(frames_array)):
                if bit_index >= data_length:
                    break
                frames_array[i] = (frames_array[i] & 0xFE) | data_bits[bit_index]
                bit_index += 1

        elif nchannels == 2 and sampwidth == 2:
            # 16-bit stereo: use only left channel low bytes (every 4th byte starting from 0)
            for i in range(0, len(frames_array), 4):
                if bit_index >= data_length:
                    break
                # Use the low byte of left channel (position i)
                frames_array[i] = (frames_array[i] & 0xFE) | data_bits[bit_index]
                bit_index += 1

        elif nchannels == 2:
            # 8-bit stereo: use only left channel (every 2nd byte)
            for i in range(0, len(frames_array), 2):
                if bit_index >= data_length:
                    break
                frames_array[i] = (frames_array[i] & 0xFE) | data_bits[bit_index]
                bit_index += 1

        else:
            # Multi-channel: use only first channel
            bytes_per_sample = nchannels * sampwidth
            for i in range(0, len(frames_array), bytes_per_sample):
                if bit_index >= data_length:
                    break
                # Use first byte of first channel
                frames_array[i] = (frames_array[i] & 0xFE) | data_bits[bit_index]
                bit_index += 1

    def _extract_audio_bits(self, frames_array: bytearray, num_bits: int, params) -> list:
        """Extract bits from audio data considering stereo configuration"""
        nchannels = params.nchannels
        sampwidth = params.sampwidth
        bits = []

        if nchannels == 1:
            # Mono: extract from all bytes
            for i in range(min(num_bits, len(frames_array))):
                bits.append(frames_array[i] & 1)

        elif nchannels == 2 and sampwidth == 2:
            # 16-bit stereo: extract from left channel low bytes
            for i in range(0, min(num_bits * 4, len(frames_array)), 4):
                if len(bits) >= num_bits:
                    break
                bits.append(frames_array[i] & 1)

        elif nchannels == 2:
            # 8-bit stereo: extract from left channel
            for i in range(0, min(num_bits * 2, len(frames_array)), 2):
                if len(bits) >= num_bits:
                    break
                bits.append(frames_array[i] & 1)

        else:
            # Multi-channel: extract from first channel
            bytes_per_sample = nchannels * sampwidth
            for i in range(0, min(num_bits * bytes_per_sample, len(frames_array)), bytes_per_sample):
                if len(bits) >= num_bits:
                    break
                bits.append(frames_array[i] & 1)

        return bits[:num_bits]

    def _prepare_data(self, secret_data: bytes, password: str, original_filename: str) -> bytes:
        """Prepare data with header and integrity check"""
        data_hash = hashlib.sha256(secret_data).digest()

        # Prepare filename
        filename_bytes = original_filename.encode('utf-8') if original_filename else b''
        filename_length = len(filename_bytes)

        data_size = len(secret_data)
        header = (self.MAGIC_BYTES +
                  struct.pack('>I', data_size) +
                  struct.pack('>H', filename_length) +
                  filename_bytes +
                  data_hash)
        header = header.ljust(self.HEADER_SIZE // 8, b'\x00')
        return header + secret_data

    def _bytes_to_bits(self, data: bytes) -> list:
        """Convert bytes to list of bits"""
        bits = []
        for byte in data:
            for i in range(8):
                bits.append((byte >> (7 - i)) & 1)
        return bits

    def _bits_to_bytes(self, bits: list) -> bytes:
        """Convert list of bits to bytes"""
        bytes_data = bytearray()
        for i in range(0, len(bits), 8):
            byte = 0
            for j in range(min(8, len(bits) - i)):
                byte = (byte << 1) | bits[i + j]
            bytes_data.append(byte)
        return bytes(bytes_data)


class StegoProBackend:

    def __init__(self):
        self.image_stego = LSBImageSteganography()
        self.audio_stego = LSBAudioSteganography()

    def process_hide_request(self, container_data: bytes, secret_data: bytes,
                             method: str, password: str = "", original_filename: str = "",
                             file_extension: str = "") -> dict:
        """
        Process hide data request
        Args:
            container_data: Container file data
            secret_data: Data to hide
            method: Steganography method ('lsb' or 'audio_lsb')
            password: Optional password
            original_filename: Original filename to preserve
            file_extension: Original file extension
        Returns:
            Dictionary with result information
        """
        try:
            if method == 'lsb':
                stego_data = self.image_stego.hide_data(container_data, secret_data, password, original_filename)
                output_extension = '.png'
            elif method == 'audio_lsb':
                stego_data = self.audio_stego.hide_data(container_data, secret_data, password, original_filename)
                output_extension = '.wav'
            else:
                raise StegoException(f"Unsupported method: {method}")

            # Encode to base64 for web transfer
            stego_base64 = base64.b64encode(stego_data).decode('utf-8')
            return {
                'success': True,
                'method': method,
                'stego_data': stego_base64,
                'file_extension': output_extension,
                'original_size': len(container_data),
                'hidden_size': len(secret_data),
                'stego_size': len(stego_data),
                'original_filename': original_filename
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def process_extract_request(self, stego_data: bytes, method: str,
                                password: str = "") -> dict:

        try:
            extracted_data = None
            original_filename = ""
            detected_method = method

            if method == 'lsb':
                extracted_data, original_filename = self.image_stego.extract_data(stego_data, password)
            elif method == 'audio_lsb':
                extracted_data, original_filename = self.audio_stego.extract_data(stego_data, password)
            else:
                # Auto-detect method
                try:
                    extracted_data, original_filename = self.image_stego.extract_data(stego_data, password)
                    detected_method = 'lsb'
                except Exception as e1:
                    try:
                        extracted_data, original_filename = self.audio_stego.extract_data(stego_data, password)
                        detected_method = 'audio_lsb'
                    except Exception as e2:
                        raise StegoException(f"Auto-detection failed: Image - {e1}, Audio - {e2}")

            # Determine file extension from original filename
            file_extension = 'bin'
            if original_filename and '.' in original_filename:
                file_extension = original_filename.split('.')[-1]

            # Encode to base64
            data_base64 = base64.b64encode(extracted_data).decode('utf-8')

            return {
                'success': True,
                'extracted_data': data_base64,
                'method': detected_method,
                'extracted_size': len(extracted_data),
                'original_filename': original_filename,
                'file_extension': file_extension
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def get_file_info(self, file_data: bytes, filename: str) -> dict:
        """Get file information for frontend"""
        try:
            file_extension = filename.split('.')[-1].lower()

            if file_extension in ['png', 'bmp', 'tiff', 'tif']:
                image = Image.open(io.BytesIO(file_data))
                return {
                    'type': 'image',
                    'format': image.format,
                    'size': len(file_data),
                    'width': image.width,
                    'height': image.height,
                    'mode': image.mode,
                    'capacity_estimate': image.width * image.height * 3 // 8  # Rough estimate
                }
            elif file_extension == 'wav':
                with wave.open(io.BytesIO(file_data), 'rb') as wav_file:
                    params = wav_file.getparams()
                    capacity = self.audio_stego._calculate_audio_capacity(
                        bytearray(wav_file.readframes(wav_file.getnframes())),
                        params
                    )
                    return {
                        'type': 'audio',
                        'format': 'WAV',
                        'size': len(file_data),
                        'channels': wav_file.getnchannels(),
                        'sample_rate': wav_file.getframerate(),
                        'duration': wav_file.getnframes() / wav_file.getframerate(),
                        'capacity_estimate': capacity // 8  # Convert bits to bytes
                    }
            else:
                return {
                    'type': 'unknown',
                    'size': len(file_data)
                }

        except Exception as e:
            return {
                'error': str(e)
            }


# Global backend instance
backend = StegoProBackend()


# Flask-like interface for the backend
def process_hide(container_b64: str, secret_b64: str, method: str, password: str = "",
                 original_filename: str = "", file_extension: str = "") -> dict:
    """Process hide request from frontend"""
    try:
        container_data = base64.b64decode(container_b64)
        secret_data = base64.b64decode(secret_b64)

        result = backend.process_hide_request(container_data, secret_data, method, password,
                                              original_filename, file_extension)
        return result

    except Exception as e:
        return {
            'success': False,
            'error': f"Processing error: {str(e)}"
        }


def process_extract(stego_b64: str, password: str = "") -> dict:
    """Process extract request from frontend"""
    try:
        stego_data = base64.b64decode(stego_b64)

        # Try to auto-detect method
        result = backend.process_extract_request(stego_data, 'auto', password)
        return result

    except Exception as e:
        return {
            'success': False,
            'error': f"Processing error: {str(e)}"
        }


def get_file_info(file_b64: str, filename: str) -> dict:
    """Get file information"""
    try:
        file_data = base64.b64decode(file_b64)
        return backend.get_file_info(file_data, filename)
    except Exception as e:
        return {
            'error': f"Failed to get file info: {str(e)}"
        }


if __name__ == "__main__":
    # Test the backend
    print("OccultoNG Backend initialized successfully!")
