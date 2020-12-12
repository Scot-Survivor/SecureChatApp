import base64
import hashlib
import struct
import os
from Crypto.Random import random
from Crypto.Cipher import AES


class AESCipher(object):

    # noinspection PyUnusedLocal
    def __init__(self, key):
        self.bs = AES.block_size
        self.key = hashlib.sha256(key).digest()
        self.iv = ''.join([chr(random.randint(0, 0xFF)) for i in range(16)]).encode()

    def encrypt(self, raw):
        raw = self._pad(raw)
        self.iv = self.iv[:self.bs]
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        return base64.b64encode(self.iv + cipher.encrypt(raw.encode()))

    def decrypt(self, enc):
        enc = base64.b64decode(enc)
        iv = enc[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self._unpad(cipher.decrypt(enc[AES.block_size:])).decode('utf-8')

    def _pad(self, s):
        return s + (self.bs - len(s) % self.bs) * chr(self.bs - len(s) % self.bs)

    def setIV(self, iv):
        self.iv = iv

    def returnIV(self):
        return self.iv

    @staticmethod
    def _unpad(s):
        return s[:-ord(s[len(s) - 1:])]

    def encrypt_file(self, in_filename, out_filename=None, chunk_size=64 * 1024):
        """ Encrypts a file using AES (CBC mode) with the
            given key.

            key:
                The encryption key - a string that must be
                either 16, 24 or 32 bytes long. Longer keys
                are more secure.

            in_filename:
                Name of the input file

            out_filename:
                If None, '<in_filename>.enc' will be used.

            chunk_size:
                Sets the size of the chunk which the function
                uses to read and encrypt the file. Larger chunk
                sizes can be faster for some files and machines.
                chunk_size must be divisible by 16.
        """
        if not out_filename:
            out_filename = in_filename + '.enc'
        self.iv = self.iv[:self.bs]
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        file_size = os.path.getsize(in_filename)

        with open(in_filename, 'rb') as infile:
            with open(out_filename, 'wb') as outfile:
                outfile.write(struct.pack('<Q', file_size))
                outfile.write(self.iv)

                while True:
                    chunk = infile.read(chunk_size)
                    if len(chunk) == 0:
                        break
                    elif len(chunk) % 16 != 0:
                        chunk += ' '.encode() * (16 - len(chunk) % 16)

                    outfile.write(cipher.encrypt(chunk))

    def decrypt_file(self, in_filename, out_filename=None, chunk_size=24 * 1024):
        """ Decrypts a file using AES (CBC mode) with the
            given key. Parameters are similar to encrypt_file,
            with one difference: out_filename, if not supplied
            will be in_filename without its last extension
            (i.e. if in_filename is 'aaa.zip.enc' then
            out_filename will be 'aaa.zip')
        """
        if not out_filename:
            out_filename = os.path.basename(os.path.splitext(in_filename)[0])

        with open(in_filename, 'rb') as infile:
            orig_size = struct.unpack('<Q', infile.read(struct.calcsize('Q')))[0]
            iv = infile.read(16)
            cipher = AES.new(self.key, AES.MODE_CBC, iv)

            with open(out_filename, 'wb') as outfile:
                while True:
                    chunk = infile.read(chunk_size)
                    if len(chunk) == 0:
                        break
                    outfile.write(cipher.decrypt(chunk))

                outfile.truncate(orig_size)
