import base64,os
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
# 필요 라이브러리 : poytre add pycryptodome
# 코드 설명 : https://github.com/sungsu05/B2Coin_algorithm/blob/master/05_30/SonSungSu/AES2.PY0

class AESAlgorithm():
    """ 암호화, 복호화 알고리즘 """
    AES_KEY = os.environ.get('AES_KEY')
    AES_KEY = bytes(AES_KEY, 'utf-8')
    @classmethod
    def encrypt_all(self,**kwargs):
        """ 암호화 """
        cipher = AES.new(self.AES_KEY, AES.MODE_ECB)
        data_dict = {}
        for key,value in kwargs.items():
            cipher_data = cipher.encrypt(pad(value.encode(), AES.block_size))
            encrypt_value = base64.b64encode(cipher_data).decode()
            data_dict[key] = encrypt_value
        return data_dict

    @classmethod
    def decrypt_all(self,**kwargs):
        """ 복호화 """
        cipher = AES.new(self.AES_KEY, AES.MODE_ECB)
        data_dict = {}
        for key, value in kwargs.items():
            cipher_data = base64.b64decode(value)
            data = unpad(cipher.decrypt(cipher_data), AES.block_size)
            cipher_value = data.decode()
            data_dict[key] = cipher_value
        return data_dict

    @classmethod
    def encrypt(self,data):
        """ 단일 데이터 암호화 """
        cipher = AES.new(self.AES_KEY, AES.MODE_ECB)
        cipher_data = cipher.encrypt(pad(data.encode(), AES.block_size))
        return base64.b64encode(cipher_data).decode()

    @classmethod
    def decrypt(self,cipher_data):
        """ 단일 데이터 복호화 """
        cipher = AES.new(self.AES_KEY, AES.MODE_ECB)
        cipher_data = base64.b64decode(cipher_data)
        data = unpad(cipher.decrypt(cipher_data), AES.block_size)
        return data.decode()
