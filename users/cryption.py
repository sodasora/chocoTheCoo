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
    def encrypt_all(cls,**kwargs):
        """ 암호화 """
        cipher = AES.new(cls.AES_KEY, AES.MODE_ECB)

        data_dict = {} # key값 특정
        for key,value in kwargs.items():
            # 분기
            cipher_data = cipher.encrypt(pad(value.encode(), AES.block_size))
            encrypt_element = base64.b64encode(cipher_data).decode()
            data_dict[key] = encrypt_element
        return data_dict
    # 키값을 기준으로

    @classmethod
    def decrypt_all(cls,**kwargs):
        """ 복호화 """
        cipher = AES.new(cls.AES_KEY, AES.MODE_ECB)
        data_dict = {}
        for key, element in kwargs.items():
            cipher_data = base64.b64decode(element)
            data = unpad(cipher.decrypt(cipher_data), AES.block_size)
            cipher_element = data.decode()
            data_dict[key] = cipher_element
        return data_dict

    @classmethod
    def encrypt(cls,data):
        """ 단일 데이터 암호화 """
        cipher = AES.new(cls.AES_KEY, AES.MODE_ECB)
        cipher_data = cipher.encrypt(pad(data.encode(), AES.block_size))
        return base64.b64encode(cipher_data).decode()

    @classmethod
    def decrypt(cls,cipher_data):
        """ 단일 데이터 복호화 """
        cipher = AES.new(cls.AES_KEY, AES.MODE_ECB)
        cipher_data = base64.b64decode(cipher_data)
        data = unpad(cipher.decrypt(cipher_data), AES.block_size)
        return data.decode()

    @classmethod
    def decrypt_userdata(cls, elements):
        """ 사용자 정보 복호화 """
        if elements.get('numbers') != None:
            """ 통관 번호 복호화 """
            numbers = AESAlgorithm.decrypt(elements['numbers'])
            elements['numbers'] = numbers
        return elements

    @classmethod
    def decrypt_deliveries(cls, elements):
        """ 배송 정보 복호화 """
        for element in elements:
            address = AESAlgorithm.decrypt(element['address'])
            detail_address = AESAlgorithm.decrypt(element['detail_address'])
            recipient = AESAlgorithm.decrypt(element['recipient'])
            postal_code = AESAlgorithm.decrypt(element['postal_code'])
            element['address'] = address
            element['detail_address'] = detail_address
            element['recipient'] = recipient
            element['postal_code'] = postal_code
        return elements

    @classmethod
    def decrypt_seller_information(cls, elements):
        """ 판매자 정보 복호화 """
        if elements != None:
            elements['company_name'] = AESAlgorithm.decrypt(elements['company_name'])
            elements['buisness_number'] = AESAlgorithm.decrypt(elements['buisness_number'])
            elements['bank_name'] = AESAlgorithm.decrypt(elements['bank_name'])
            elements['account_number'] = AESAlgorithm.decrypt(elements['account_number'])
            elements['business_owner_name'] = AESAlgorithm.decrypt(elements['business_owner_name'])
            elements['account_holder'] = AESAlgorithm.decrypt(elements['account_holder'])
            elements['contact_number'] = AESAlgorithm.decrypt(elements['contact_number'])
        return elements

    @classmethod
    def decrypt_profile_information(cls, elements):
        """ 프로필 정보 데이터 복호화 """
        if elements.get('numbers') is not None:
            """ 통관 번호 복호화 """
            numbers = AESAlgorithm.decrypt(elements['numbers'])
            elements['numbers'] = numbers

        for element in elements['deliveries_data']:
            """ 배송 정보 복호화 """
            address = AESAlgorithm.decrypt(element['address'])
            detail_address = AESAlgorithm.decrypt(element['detail_address'])
            recipient = AESAlgorithm.decrypt(element['recipient'])
            postal_code = AESAlgorithm.decrypt(element['postal_code'])
            element['address'] = address
            element['detail_address'] = detail_address
            element['recipient'] = recipient
            element['postal_code'] = postal_code
        return elements