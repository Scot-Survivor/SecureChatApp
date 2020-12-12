from encryption import AESCipher
import os

key = os.urandom(64)
cipher = AESCipher(key)

cipher.encrypt_file(in_filename='2020-06-05_19.11.40.png', out_filename='uploads/larger-image.enc')

cipher.decrypt_file(in_filename='uploads/larger-image.enc', out_filename='uploads/larger-image.png')

print("Done")
