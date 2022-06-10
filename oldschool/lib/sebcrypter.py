"""Sebcrypter"""
# 27/11/2021
import os,random

# CONSTANTS
KEYFILESIZE = 4096
BO = "little"  # byte order for byte-int conversions


def keygen(fileName = None) -> bytes:
    """Generates a new random key"""
    allvalues = list(range(2048))
    key = bytes()
    key += b'SEBK'
    while allvalues:
        r = random.randint(0, len(allvalues)-1)
        value = allvalues.pop(r)
        bytevalue = value.to_bytes(2, BO)
        key += bytevalue
    if fileName:
        with open(fileName,"w") as keyf:
            keyf.write(key)
    return key


def readkey(keyfile="key.seb",key=None) -> list:
    """Reads the contents of a key file and converts it
    can be used with either byte format key or key file name"""
    if key:
        content = key[4:]
    elif os.path.exists(keyfile):
        with open(keyfile, 'rb') as keyf:
            if keyf.read(4) != b'SEBK':
                raise ValueError("The file is not a key file")
            content = keyf.read()
    else:
        raise FileNotFoundError(keyfile)
    if len(content) == KEYFILESIZE:
        keytab = []
        for i in range(256):
            values = []
            for j in range(8):
                bytevalue = content[((i*8)+j)*2:((i*8)+j+1)*2]
                value = int.from_bytes(bytevalue, BO)
                values.append(value)
            keytab.append(tuple(values))
        return keytab
    else:
        raise ValueError("Damaged or invalid file name or key")


def encrypt(value: bytes, key: list) -> bytes:
    """Encrypts the given value by key"""
    encryptedvalue = bytes()
    for va in value:
        r = random.choice(key[va])
        encryptedvalue += r.to_bytes(2, BO)
        continue
    return encryptedvalue


def decrypt(value: bytes, key: list) -> bytes:
    """Decrypts the given value by key"""
    decryptedvalue = bytes()
    valuelen = len(value)
    for i in range(valuelen//2):
        bytevalue = value[i*2:(i+1)*2]
        intvalue = int.from_bytes(bytevalue, BO)
        ind = 0
        for values in key:
            if intvalue in values:
                decryptedvalue += ind.to_bytes(1, BO)
                break
            ind += 1
    return decryptedvalue
