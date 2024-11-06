import hashlib

def hash_key(key : str):
    return hashlib.md5(key.encode('utf-8')).hexdigest()