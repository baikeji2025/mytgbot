# 文件名：福建健康头像下载_单次版.py
# 描述：用于下载福建健康头像的单次执行版本，自动安装所需库
# 使用方法：将身份证号直接输入或保存到sfz.txt文件中

import sys
import subprocess
import pkg_resources

# 自动安装缺少的库
required_packages = ['requests']

def install_packages():
    """安装所需的库"""
    installed_packages = {pkg.key for pkg in pkg_resources.working_set}
    missing_packages = [pkg for pkg in required_packages if pkg.lower() not in installed_packages]
    
    if missing_packages:
        print("正在安装所需的库...")
        for package in missing_packages:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                print(f"✓ 成功安装 {package}")
            except subprocess.CalledProcessError:
                print(f"✗ 安装 {package} 失败，请手动安装: pip install {package}")
                sys.exit(1)

# 安装基础库
install_packages()

# 导入基础库
import requests
import base64
import json
import os
import random
import string

# 尝试导入加密库，如果失败则提供替代方案
CRYPTO_AVAILABLE = False
try:
    # 先尝试 pycryptodome
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad, unpad
    CRYPTO_AVAILABLE = True
    print("✓ 已加载 pycryptodome 库")
except ImportError:
    try:
        # 尝试 cryptography 库
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.primitives import padding
        from cryptography.hazmat.backends import default_backend
        CRYPTO_AVAILABLE = True
        CRYPTO_TYPE = 'cryptography'
        print("✓ 已加载 cryptography 库")
    except ImportError:
        # 尝试 pure-python 实现
        try:
            # 如果以上都失败，使用纯Python实现
            print("正在使用纯Python加密实现...")
            CRYPTO_AVAILABLE = True
            CRYPTO_TYPE = 'pure'
        except:
            print("✗ 无法加载任何加密库")
            print("请手动安装以下任一库：")
            print("1. pip install pycryptodome")
            print("2. pip install cryptography")
            input("按回车键退出...")
            sys.exit(1)

AES_KEY = "ylzyw@2018@12345"

# 根据可用的库选择加密实现
if CRYPTO_AVAILABLE:
    if 'CRYPTO_TYPE' in locals() and CRYPTO_TYPE == 'cryptography':
        # 使用 cryptography 库的实现
        def aes_ecb_encrypt(text, key=AES_KEY):
            """AES ECB加密 - cryptography版本"""
            key_bytes = key.encode('utf-8')[:16]
            text_bytes = text.encode('utf-8')
            
            # 使用PKCS7填充
            padder = padding.PKCS7(128).padder()
            padded_text = padder.update(text_bytes) + padder.finalize()
            
            cipher = Cipher(algorithms.AES(key_bytes), modes.ECB(), backend=default_backend())
            encryptor = cipher.encryptor()
            encrypted_bytes = encryptor.update(padded_text) + encryptor.finalize()
            
            return base64.b64encode(encrypted_bytes).decode('utf-8')
        
        def aes_ecb_decrypt(encrypted_text, key=AES_KEY):
            """AES ECB解密 - cryptography版本"""
            key_bytes = key.encode('utf-8')[:16]
            encrypted_bytes = base64.b64decode(encrypted_text)
            
            cipher = Cipher(algorithms.AES(key_bytes), modes.ECB(), backend=default_backend())
            decryptor = cipher.decryptor()
            decrypted_bytes = decryptor.update(encrypted_bytes) + decryptor.finalize()
            
            # 去除PKCS7填充
            unpadder = padding.PKCS7(128).unpadder()
            unpadded_bytes = unpadder.update(decrypted_bytes) + unpadder.finalize()
            
            return unpadded_bytes.decode('utf-8')
    
    elif 'CRYPTO_TYPE' in locals() and CRYPTO_TYPE == 'pure':
        # 纯Python实现（简单版本，可能不适用于所有情况）
        def aes_ecb_encrypt(text, key=AES_KEY):
            """AES ECB加密 - 纯Python版本（简化）"""
            print("警告：使用简化加密，可能无法正常工作")
            # 这里简化处理，实际使用时应该用完整的AES实现
            return base64.b64encode(text.encode()).decode()
        
        def aes_ecb_decrypt(encrypted_text, key=AES_KEY):
            """AES ECB解密 - 纯Python版本（简化）"""
            print("警告：使用简化解密，可能无法正常工作")
            # 这里简化处理，实际使用时应该用完整的AES实现
            return base64.b64decode(encrypted_text).decode()
    
    else:
        # 使用 pycryptodome 的实现
        def aes_ecb_encrypt(text, key=AES_KEY):
            """AES ECB加密 - pycryptodome版本"""
            key_bytes = key.encode('utf-8')[:16]
            text_bytes = text.encode('utf-8')
            padded_text = pad(text_bytes, AES.block_size, style='pkcs7')
            cipher = AES.new(key_bytes, AES.MODE_ECB)
            encrypted_bytes = cipher.encrypt(padded_text)
            return base64.b64encode(encrypted_bytes).decode('utf-8')
        
        def aes_ecb_decrypt(encrypted_text, key=AES_KEY):
            """AES ECB解密 - pycryptodome版本"""
            key_bytes = key.encode('utf-8')[:16]
            encrypted_bytes = base64.b64decode(encrypted_text)
            cipher = AES.new(key_bytes, AES.MODE_ECB)
            decrypted_bytes = cipher.decrypt(encrypted_bytes)
            return unpad(decrypted_bytes, AES.block_size, style='pkcs7').decode('utf-8')
else:
    print("✗ 没有可用的加密库")
    sys.exit(1)

def fix_image_url(path):
    """修复图片URL"""
    base_url = "https://www.fjweijian.com/hc-applet"
    if not path:
        return ""
    path = path.replace("//", "/").replace("/images", "images", 1)
    if not path.startswith("/"):
        path = "/" + path
    return f"{base_url}{path}"

def download_image(url, save_path):
    """下载图片"""
    if not url:
        print("无有效图片URL")
        return False
    
    try:
        # 设置超时和重试
        response = requests.get(url, stream=True, timeout=15)
        if response.status_code == 200:
            # 检查文件大小
            total_size = int(response.headers.get('content-length', 0))
            
            with open(save_path, 'wb') as f:
                if total_size == 0:
                    f.write(response.content)
                else:
                    downloaded = 0
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            # 显示进度
                            progress = (downloaded / total_size) * 100 if total_size > 0 else 0
                            print(f"下载进度: {progress:.1f}%", end='\r')
            print(f"\n✓ 图片已保存: {save_path}")
            return True
        else:
            print(f"✗ 图片下载失败，状态码: {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"✗ 下载超时: {url}")
        return False
    except Exception as e:
        print(f"✗ 图片下载出错: {str(e)}")
        return False

def generate_random_id(length=28):
    """生成随机ID"""
    chars = string.ascii_letters + string.digits
    return 'o' + ''.join(random.choice(chars) for _ in range(length-1))

def query_first_api(identity_id):
    """查询第一个接口获取用户信息"""
    request_data = {
        "hthReserveCardNo": "",
        "hthCustomerIdentityId": identity_id
    }
    
    try:
        plaintext = json.dumps(request_data, ensure_ascii=False)
        encrypted_request = aes_ecb_encrypt(plaintext)
    except Exception as e:
        print(f"✗ 加密请求数据失败: {str(e)}")
        return None
    
    url = "https://www.fjweijian.com/health-system/wechat?act=hthFindList&g="
    headers = {
        "Host": "www.fjweijian.com",
        "Content-Type": "application/json;charset=utf-8",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.fjweijian.com/",
        "Accept": "application/json"
    }
    
    try:
        print(f"发送请求到: {url}")
        response = requests.post(url, headers=headers, data=encrypted_request, timeout=15)
        print(f"收到响应，状态码: {response.status_code}")
        
        if response.status_code != 200:
            print(f"✗ 请求失败，状态码: {response.status_code}")
            return None
            
        # 处理响应
        response_text = response.text.strip('"')
        print(f"响应长度: {len(response_text)} 字符")
        
        decrypted_response = aes_ecb_decrypt(response_text)
        return json.loads(decrypted_response)
        
    except requests.exceptions.Timeout:
        print("✗ 请求超时")
        return None
    except Exception as e:
        print(f"✗ 接口请求失败: {str(e)}")
        return None

def query_second_api(user_info):
    """查询第二个接口获取头像"""
    random_id = generate_random_id()
    
    request_data = {
        "id": random_id,
        "userRealName": user_info.get("姓名", ""),
        "userIdNumber": user_info.get("身份证号", ""),
        "hthPersonPhone": user_info.get("手机号", ""),
        "idNumType": "0"
    }
    
    try:
        plaintext = json.dumps(request_data, ensure_ascii=False)
        encrypted_payload = aes_ecb_encrypt(plaintext)
    except Exception as e:
        print(f"✗ 加密请求数据失败: {str(e)}")
        return None
    
    url = "https://www.fjweijian.com/hc-applet/applet?act=userBind&g=&i=0.14438454991011718"
    headers = {
        "Host": "www.fjweijian.com",
        "Connection": "keep-alive",
        "Content-Type": "application/json;charset=UTF-8",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://servicewechat.com/wx589cfb7a57cb6382/30/page-frame.html",
        "Accept": "application/json"
    }
    
    try:
        print(f"发送请求到: {url}")
        response = requests.post(url, headers=headers, data=encrypted_payload, timeout=15)
        print(f"收到响应，状态码: {response.status_code}")
        
        if response.status_code != 200:
            print(f"✗ 请求失败，状态码: {response.status_code}")
            return None
            
        response_text = response.text.strip('"')
        print(f"响应长度: {len(response_text)} 字符")
        
        decrypted = aes_ecb_decrypt(response_text)
        return json.loads(decrypted)
        
    except requests.exceptions.Timeout:
        print("✗ 请求超时")
        return None
    except Exception as e:
        print(f"✗ 接口请求失败: {str(e)}")
        return None

def process_identity_id(identity_id):
    """处理单个身份证号"""
    print(f"\n{'='*60}")
    print(f"正在处理身份证号: {identity_id}")
    print(f"{'='*60}")
    
    # 验证身份证号格式
    if len(identity_id) != 18:
        print(f"✗ 身份证号长度不正确: {len(identity_id)}位 (应为18位)")
        return False
    
    # 查询第一个接口
    print("1. 查询用户信息...")
    first_response = query_first_api(identity_id)
    
    if not first_response:
        print("✗ 无法获取用户信息")
        return False
    
    # 检查响应格式
    if not isinstance(first_response, dict):
        print("✗ 响应格式不正确")
        return False
    
    if first_response.get("code") != "10000":
        print(f"✗ 接口返回错误: {first_response.get('code')} - {first_response.get('message', '未知错误')}")
        return False
    
    # 提取用户信息
    user_info = {
        "姓名": "",
        "身份证号": identity_id,
        "手机号": ""
    }
    
    if first_response.get("rows") and isinstance(first_response["rows"], list) and len(first_response["rows"]) > 0:
        row = first_response["rows"][0]
        user_info["姓名"] = row.get("hthCustomerNname", "")
        user_info["手机号"] = row.get("hthPersonPhone", "")
        
    print(f"   姓名: {user_info['姓名'] or '未获取到'}")
    print(f"   手机号: {user_info['手机号'] or '未获取到'}")
    
    if not user_info["姓名"]:
        print("⚠ 警告：未获取到姓名，可能影响后续查询")
    
    # 查询第二个接口
    print("2. 查询头像信息...")
    second_response = query_second_api(user_info)
    
    if not second_response:
        return False
    
    # 检查第二个接口响应
    if not isinstance(second_response, dict):
        print("✗ 第二个接口响应格式不正确")
        return False
    
    # 下载图片
    image_url = None
    try:
        if second_response.get("vo", {}).get("hthChkPermitRVo", {}).get("hthPhoto"):
            image_url = fix_image_url(second_response["vo"]["hthChkPermitRVo"]["hthPhoto"])
    except Exception as e:
        print(f"✗ 解析图片URL失败: {str(e)}")
    
    if image_url:
        print(f"3. 下载头像...")
        print(f"   图片URL: {image_url}")
        
        # 创建输出目录
        os.makedirs("output", exist_ok=True)
        
        # 保存图片
        if user_info['姓名']:
            save_name = f"{user_info['姓名']}_{identity_id}.jpg"
        else:
            save_name = f"{identity_id}.jpg"
        
        # 清理文件名中的非法字符
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            save_name = save_name.replace(char, '_')
        
        save_path = os.path.join("output", save_name)
        
        # 如果文件已存在，添加序号
        if os.path.exists(save_path):
            base_name, ext = os.path.splitext(save_name)
            counter = 1
            while os.path.exists(os.path.join("output", f"{base_name}_{counter}{ext}")):
                counter += 1
            save_name = f"{base_name}_{counter}{ext}"
            save_path = os.path.join("output", save_name)
        
        if download_image(image_url, save_path):
            return True
        else:
            return False
    else:
        print("✗ 未找到头像信息")
        print(f"响应内容: {json.dumps(second_response, ensure_ascii=False, indent=2)}")
        return False

def single_mode():
    """单次模式：手动输入身份证号"""
    print("欢迎使用福建健康头像下载工具（单次版）")
    print("功能说明：输入身份证号，下载对应的健康头像")
    print("退出方式：输入 q 或 quit\n")
    
    while True:
        identity_id = input("请输入身份证号（或输入 q 退出）: ").strip()
        
        if identity_id.lower() in ['q', 'quit', 'exit']:
            print("感谢使用，再见！")
            break
            
        if len(identity_id) != 18:
            print("✗ 身份证号长度不正确，应为18位")
            continue
            
        # 处理身份证号
        success = process_identity_id(identity_id)
        
        if success:
            print(f"✓ 处理完成: {identity_id}")
        else:
            print(f"✗ 处理失败: {identity_id}")
        
        print()  # 空行分隔

def batch_mode():
    """批量模式：从文件读取身份证号"""
    print("批量模式：从sfz.txt文件读取身份证号")
    
    if not os.path.exists("sfz.txt"):
        print("✗ 未找到sfz.txt文件")
        print("请在程序目录下创建sfz.txt文件，每行输入一个身份证号")
        print("示例：")
        print("350102199001011234")
        print("350102199002022345")
        return
    
    try:
        with open("sfz.txt", "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        identity_ids = []
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if line:
                if line.startswith('#') or line.startswith('//'):
                    continue  # 跳过注释
                identity_ids.append(line)
            
        if not identity_ids:
            print("✗ sfz.txt文件中没有找到有效的身份证号")
            return
        
        print(f"找到 {len(identity_ids)} 个身份证号")
        
        success_count = 0
        fail_count = 0
        
        for i, identity_id in enumerate(identity_ids, 1):
            print(f"\n[{i}/{len(identity_ids)}] ", end="")
            
            if len(identity_id) != 18:
                print(f"✗ 跳过无效身份证号: {identity_id} (长度: {len(identity_id)}位)")
                fail_count += 1
                continue
                
            success = process_identity_id(identity_id)
            
            if success:
                success_count += 1
            else:
                fail_count += 1
        
        print(f"\n{'='*60}")
        print(f"处理完成！")
        print(f"成功: {success_count} 个")
        print(f"失败: {fail_count} 个")
        
        if success_count > 0:
            print(f"图片已保存到 output 文件夹")
            os.system(f'explorer "{os.path.abspath("output")}"')
        
    except Exception as e:
        print(f"✗ 读取文件出错: {str(e)}")

def test_connection():
    """测试网络连接"""
    print("测试网络连接...")
    try:
        response = requests.get("https://www.fjweijian.com", timeout=10)
        if response.status_code == 200:
            print("✓ 网络连接正常")
            return True
        else:
            print(f"✗ 网络连接异常，状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ 网络连接失败: {str(e)}")
        return False

def main():
    """主函数"""
    print("福建健康头像下载工具 v1.1")
    print("=" * 60)
    
    # 测试网络连接
    if not test_connection():
        print("⚠ 警告：网络连接可能有问题，请检查网络")
        choice = input("是否继续？(y/n): ").lower()
        if choice != 'y':
            return
    
    print("\n请选择模式：")
    print("1. 单次输入模式（手动输入身份证号）")
    print("2. 批量处理模式（从sfz.txt文件读取）")
    print("3. 测试模式（测试单个身份证号）")
    print("4. 退出")
    
    while True:
        choice = input("\n请选择模式 (1/2/3/4): ").strip()
        
        if choice == "1":
            single_mode()
            break
        elif choice == "2":
            batch_mode()
            break
        elif choice == "3":
            # 测试模式
            test_id = input("请输入测试用的身份证号: ").strip()
            if test_id:
                print("\n测试模式开始...")
                process_identity_id(test_id)
            break
        elif choice == "4":
            print("感谢使用，再见！")
            break
        else:
            print("✗ 无效选择，请输入 1、2、3 或 4")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n程序被用户中断")
    except Exception as e:
        print(f"\n发生未知错误: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        input("\n按回车键退出...")
