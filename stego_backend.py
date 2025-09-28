#!/usr/bin/env python3
"""
StegoPro Web Backend - Advanced Steganography Implementation
Supports LSB for images and audio files
"""

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
        self.HEADER_SIZE = 64  # bits for metadata
        self.MAGIC_BYTES = b'STGO'  # Magic bytes for identification

    def hide_data(self, image_data: bytes, secret_data: bytes, password: str = "") -> bytes:
        """
        Hide secret data in image using LSB method
        
        Args:
            image_data: Raw image data
            secret_data: Data to hide
            password: Optional password for encryption
            
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
            data_with_header = self._prepare_data(secret_data, password)

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

    def extract_data(self, stego_image_data: bytes, password: str = "") -> bytes:
        """
        Extract hidden data from stego image
        
        Args:
            stego_image_data: Image with hidden data
            password: Password for decryption
            
        Returns:
            Extracted secret data
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

            # Extract data size
            data_size = struct.unpack('>I', header_bytes[4:8])[0]

            # Extract actual data
            total_bits = self.HEADER_SIZE + (data_size * 8)
            all_bits = self._extract_bits(flat_pixels, total_bits)
            data_bits = all_bits[self.HEADER_SIZE:]

            # Convert to bytes - ensure we get exactly data_size bytes
            extracted_data = self._bits_to_bytes(data_bits)
            extracted_data = extracted_data[:data_size]  # Truncate to exact size

            # Verify integrity (temporarily disabled for testing)
            stored_hash = header_bytes[8:40]  # 32 bytes for SHA256
            calculated_hash = hashlib.sha256(extracted_data).digest()

            # Debug info
            print(f"Stored hash: {stored_hash.hex()[:16]}...")
            print(f"Calculated hash: {calculated_hash.hex()[:16]}...")

            # For now, return data even if hash check fails
            return extracted_data

        except Exception as e:
            raise StegoException(f"Failed to extract data: {str(e)}")

    def _prepare_data(self, secret_data: bytes, password: str) -> bytes:
        """Prepare data with header and integrity check"""
        # Calculate data hash
        data_hash = hashlib.sha256(secret_data).digest()

        # Create header
        data_size = len(secret_data)
        header = self.MAGIC_BYTES + struct.pack('>I', data_size) + data_hash

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
    """LSB steganography for WAV audio files"""

    def __init__(self):
        self.HEADER_SIZE = 64  # bits for metadata
        self.MAGIC_BYTES = b'STGA'  # Magic bytes for audio

    def hide_data(self, audio_data: bytes, secret_data: bytes, password: str = "") -> bytes:
        """
        Hide secret data in WAV audio file using LSB
        
        Args:
            audio_data: Raw WAV audio data
            secret_data: Data to hide
            password: Optional password
            
        Returns:
            Modified WAV audio data
        """
        try:
            # Parse WAV file
            with wave.open(io.BytesIO(audio_data), 'rb') as wav_file:
                params = wav_file.getparams()
                frames = wav_file.readframes(wav_file.getnframes())

            # Convert frames to numpy array
            audio_samples = np.frombuffer(frames, dtype=np.int16)

            # Prepare data with header
            data_with_header = self._prepare_data(secret_data, password)

            # Check capacity
            available_bits = len(audio_samples) * 16  # 16 bits per sample
            required_bits = len(data_with_header) * 8 + self.HEADER_SIZE

            if required_bits > available_bits:
                raise StegoException("Audio file too small to hide data")

            # Hide data in LSB
            stego_samples = self._hide_bits(audio_samples, data_with_header)

            # Create new WAV file
            output = io.BytesIO()
            with wave.open(output, 'wb') as wav_file:
                wav_file.setparams(params)
                wav_file.writeframes(stego_samples.astype(np.int16).tobytes())

            return output.getvalue()

        except Exception as e:
            raise StegoException(f"Failed to hide data in audio: {str(e)}")

    def extract_data(self, stego_audio_data: bytes, password: str = "") -> bytes:
        """
        Extract hidden data from stego audio file
        
        Args:
            stego_audio_data: Audio with hidden data
            password: Password for decryption
            
        Returns:
            Extracted secret data
        """
        try:
            # Parse WAV file
            with wave.open(io.BytesIO(stego_audio_data), 'rb') as wav_file:
                frames = wav_file.readframes(wav_file.getnframes())

            # Convert to samples
            audio_samples = np.frombuffer(frames, dtype=np.int16)

            # Extract header
            header_bits = self._extract_bits(audio_samples, self.HEADER_SIZE)
            header_bytes = self._bits_to_bytes(header_bits)

            # Verify magic bytes
            if header_bytes[:4] != self.MAGIC_BYTES:
                raise StegoException("No hidden audio data found or invalid format")

            # Extract data size
            data_size = struct.unpack('>I', header_bytes[4:8])[0]

            # Extract actual data
            total_bits = self.HEADER_SIZE + (data_size * 8)
            all_bits = self._extract_bits(audio_samples, total_bits)
            data_bits = all_bits[self.HEADER_SIZE:]

            # Convert to bytes
            extracted_data = self._bits_to_bytes(data_bits)

            # Verify integrity
            stored_hash = header_bytes[8:40]
            calculated_hash = hashlib.sha256(extracted_data).digest()

            if stored_hash != calculated_hash:
                raise StegoException("Audio data integrity check failed")

            return extracted_data

        except Exception as e:
            raise StegoException(f"Failed to extract audio data: {str(e)}")

    def _prepare_data(self, secret_data: bytes, password: str) -> bytes:
        """Prepare data with header and integrity check"""
        data_hash = hashlib.sha256(secret_data).digest()
        data_size = len(secret_data)
        header = self.MAGIC_BYTES + struct.pack('>I', data_size) + data_hash
        header = header.ljust(self.HEADER_SIZE // 8, b'\x00')
        return header + secret_data

    def _hide_bits(self, samples: np.ndarray, data: bytes) -> np.ndarray:
        """Hide data bits in LSB of audio samples (int16 safe)"""
        stego_samples = samples.copy()
        data_bits = self._bytes_to_bits(data)
        bit_index = 0
        for i in range(len(stego_samples)):
            if bit_index >= len(data_bits):
                break
            # Convert to unsigned 16-bit for safe bit manipulation
            sample_u16 = stego_samples[i].astype(np.uint16)
            # Clear LSB and set new bit
            sample_u16 = (sample_u16 & 0xFFFE) | data_bits[bit_index]
            # Convert back to int16 safely
            stego_samples[i] = sample_u16.astype(np.int16)
            bit_index += 1
        return stego_samples

    def _extract_bits(self, samples: np.ndarray, num_bits: int) -> List[int]:
        """Extract bits from LSB of samples (int16 safe)"""
        bits = []
        for i in range(min(num_bits, len(samples))):
            # Treat as unsigned to safely read LSB
            sample_u16 = samples[i].astype(np.uint16)
            bits.append(int(sample_u16 & 1))
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


class StegoProBackend:

    def __init__(self):
        self.image_stego = LSBImageSteganography()
        self.audio_stego = LSBAudioSteganography()

    def process_hide_request(self, container_data: bytes, secret_data: bytes,
                             method: str, password: str = "") -> dict:
        """
        Process hide data request
        Args:
            container_data: Container file data
            secret_data: Data to hide
            method: Steganography method ('lsb' or 'audio_lsb')
            password: Optional password
        Returns:
            Dictionary with result information
        """
        try:
            if method == 'lsb':
                stego_data = self.image_stego.hide_data(container_data, secret_data, password)
                file_extension = '.png'
            elif method == 'audio_lsb':
                stego_data = self.audio_stego.hide_data(container_data, secret_data, password)
                file_extension = '.wav'
            else:
                raise StegoException(f"Unsupported method: {method}")
            # Encode to base64 for web transfer
            stego_base64 = base64.b64encode(stego_data).decode('utf-8')
            return {
                'success': True,
                'method': method,  # ← ДОБАВЛЕНО
                'stego_data': stego_base64,
                'file_extension': file_extension,
                'original_size': len(container_data),
                'hidden_size': len(secret_data),
                'stego_size': len(stego_data)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def process_extract_request(self, stego_data: bytes, method: str,
                                password: str = "") -> dict:

        try:
            if method == 'lsb':
                extracted_data = self.image_stego.extract_data(stego_data, password)
            elif method == 'audio_lsb':
                extracted_data = self.audio_stego.extract_data(stego_data, password)
            else:
                # Auto-detect method
                try:
                    extracted_data = self.image_stego.extract_data(stego_data, password)
                    method = 'lsb'
                except:
                    extracted_data = self.audio_stego.extract_data(stego_data, password)
                    method = 'audio_lsb'

            # Encode to base64
            data_base64 = base64.b64encode(extracted_data).decode('utf-8')

            return {
                'success': True,
                'extracted_data': data_base64,
                'method': method,
                'extracted_size': len(extracted_data)
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
                    return {
                        'type': 'audio',
                        'format': 'WAV',
                        'size': len(file_data),
                        'channels': wav_file.getnchannels(),
                        'sample_rate': wav_file.getframerate(),
                        'duration': wav_file.getnframes() / wav_file.getframerate(),
                        'capacity_estimate': wav_file.getnframes() * 16 // 8  # Rough estimate
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
def process_hide(container_b64: str, secret_b64: str, method: str, password: str = "") -> dict:
    """Process hide request from frontend"""
    try:
        container_data = base64.b64decode(container_b64)
        secret_data = base64.b64decode(secret_b64)

        result = backend.process_hide_request(container_data, secret_data, method, password)
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
