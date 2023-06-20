import base64
import os
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from binascii import Error

# 필요 라이브러리 : poytre add pycryptodome
# 코드 설명 : https://github.com/sungsu05/B2Coin_algorithm/blob/master/05_30/SonSungSu/AES2.PY0

class AESAlgorithm:
    """
    암호화, 복호화 알고리즘
    """
    AES_KEY = os.environ.get('AES_KEY')
    AES_KEY = bytes(AES_KEY, 'utf-8')

    @classmethod
    def encrypt_all(cls, **kwargs):
        """
        암호화
        """
        cipher = AES.new(cls.AES_KEY, AES.MODE_ECB)
        BASIC_DATA = ['user','company_name', 'business_number', 'business_owner_name', 'contact_number', 'company_img','orders',]
        data_dict = {}  # key값 특정
        for key, value in kwargs.items():
            if key in BASIC_DATA:
                continue
            cipher_data = cipher.encrypt(pad(value.encode(), AES.block_size))
            encrypt_element = base64.b64encode(cipher_data).decode()
            data_dict[key] = encrypt_element
        return data_dict

    # 키값을 기준으로

    @classmethod
    def decrypt_all(cls, **kwargs):
        """
        복호화
        """

        cipher = AES.new(cls.AES_KEY, AES.MODE_ECB)
        data_dict = {}
        for key, value in kwargs.items():
            try:
                cipher_data = base64.b64decode(value)
                data = unpad(cipher.decrypt(cipher_data), AES.block_size)
                cipher_element = data.decode()
                data_dict[key] = cipher_element
            except TypeError:
                data_dict[key] = value
            except Error:
                data_dict[key] = value
            except ValueError:
                data_dict[key] = value
        return data_dict

    @classmethod
    def decrypt_deliveries(cls, elements):
        """ 배송 정보 복호화 """
        data_dict ={}
        for key,value in enumerate(elements):
            new_data = AESAlgorithm.decrypt_all(**value)
            data_dict[key] = new_data
        return data_dict


    @classmethod
    def encrypt(cls,data):
        """ 단일 데이터 암호화 """
        cipher = AES.new(cls.AES_KEY, AES.MODE_ECB)
        cipher_data = cipher.encrypt(pad(data.encode(), AES.block_size))
        return base64.b64encode(cipher_data).decode()

    @classmethod
    def decrypt(cls, cipher_data):
        """ 단일 데이터 복호화 """
        cipher = AES.new(cls.AES_KEY, AES.MODE_ECB)
        cipher_data = base64.b64decode(cipher_data)
        data = unpad(cipher.decrypt(cipher_data), AES.block_size)
        return data.decode()