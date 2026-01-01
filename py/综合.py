import requests
from bs4 import BeautifulSoup
import re

def search_content(query, start_page=0):
    """
    搜索指定内容
    
    Args:
        query: 用户输入的搜索内容
        start_page: 起始页数，默认为0
    """
    url = "https://baikeji2025.ccccocccc.cc/%E7%BB%BC%E5%90%88.php"
    
    payload = {
        'action': "continue",
        'currentFileIndex': str(start_page),
        'searchedFiles': "",
        'searchState': "searching",
        'query': query
    }
    
    headers = {
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 QuarkPC/6.1.0.653",
        'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        'Accept-Encoding': "gzip, deflate, br, zstd",
        'Cache-Control': "max-age=0",
        'sec-ch-ua': "\"Not?A_Brand\";v=\"99\", \"Chromium\";v=\"130\"",
        'sec-ch-ua-mobile': "?0",
        'sec-ch-ua-platform': "\"Windows\"",
        'Origin': "https://baikeji2025.ccccocccc.cc",
        'x-uctiming-46938875': "1767241806834",
        'Upgrade-Insecure-Requests': "1",
        'Sec-Fetch-Site': "same-origin",
        'Sec-Fetch-Mode': "navigate",
        'Sec-Fetch-Dest': "document",
        'Accept-Language': "zh-CN,zh;q=0.9",
        'Referer': "https://baikeji2025.ccccocccc.cc/%E7%BB%BC%E5%90%88.php",
        'Cookie': "__itrace_wid=322716c1-a8fc-4b66-9059-5077c0928fff; __test=7a978a8ccbcd0e61b6e7a62c07b85c04"
    }
    
    try:
        print(f"正在搜索第 {start_page} 页...")
        response = requests.post(url, data=payload, headers=headers)
        
        if response.status_code == 200:
            return parse_results(response.text, start_page)
        else:
            print(f"请求失败，状态码: {response.status_code}")
            return None, None
            
    except Exception as e:
        print(f"发生错误: {e}")
        return None, None

def parse_results(html_content, current_page):
    """
    解析HTML内容，提取匹配结果
    
    Args:
        html_content: HTML页面内容
        current_page: 当前页数
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 1. 提取状态信息
    status_bar = soup.select_one('.status-bar')
    if status_bar:
        status_items = status_bar.select('.status-item')
        if len(status_items) >= 4:
            total_files = status_items[0].select_one('.status-value').text
            checked_files = status_items[1].select_one('.status-value').text
            remaining_files = status_items[2].select_one('.status-value').text
            matched_files = status_items[3].select_one('.status-value').text
            
            print(f"\n=== 状态信息 ===")
            print(f"总文件数: {total_files}")
            print(f"已检查: {checked_files}")
            print(f"待检查: {remaining_files}")
            print(f"已匹配文件: {matched_files}")
    
    # 2. 提取当前文件信息
    current_file = soup.select_one('.current-file')
    if current_file:
        filename = current_file.select_one('.filename')
        file_meta = current_file.select_one('.file-meta')
        
        print(f"\n=== 当前文件信息 ===")
        if filename:
            print(f"文件名: {filename.text}")
        if file_meta:
            print(f"文件信息: {file_meta.text.strip()}")
    
    # 3. 检查是否有匹配结果
    no_matches = soup.select_one('.no-matches')
    matches_container = soup.select_one('.matches-container')
    
    # 提取匹配结果
    matches = []
    if matches_container:
        # 提取匹配数量
        match_header = matches_container.find('h3')
        if match_header:
            match_count_text = match_header.text
            print(f"\n=== {match_count_text} ===")
        
        # 提取所有匹配项
        match_items = matches_container.select('.match-item')
        for i, match_item in enumerate(match_items, 1):
            # 提取位置信息
            position = match_item.select_one('.match-position')
            # 提取内容
            content = match_item.select_one('.match-content')
            
            if position and content:
                match_info = {
                    '编号': i,
                    '位置': position.text.strip(),
                    '内容': content.get_text(strip=True)
                }
                matches.append(match_info)
        
        if matches:
            print(f"找到 {len(matches)} 条匹配记录:")
            for match in matches[:91780]:  
                print(f"{match['编号']}. {match['位置']}: {match['内容']}")
            
            if len(matches) > 10:
                print(f"... 还有 {len(matches)-10} 条记录未显示")
    
    # 4. 检查是否没有匹配
    has_matches = bool(matches)
    has_no_matches = bool(no_matches)
    
    # 5. 提取下一页的索引
    next_page = current_page + 1
    
    # 尝试从脚本中提取下一页索引
    scripts = soup.find_all('script')
    for script in scripts:
        script_text = script.string
        if script_text and 'currentFileIndex' in script_text:
            # 使用正则表达式提取页码
            pattern = r"currentFileIndex.*?value.*?'(\d+)'"
            match = re.search(pattern, script_text)
            if match:
                next_page = int(match.group(1))
                break
    
    return has_matches, next_page, matches

def main():
    """主函数"""
    print("=== 白科技综合搜索工具 ===")
    
    # 1. 获取用户输入
    query = input("请输入要搜索的内容: ").strip()
    if not query:
        print("搜索内容不能为空！")
        return
    
    # 2. 设置起始页
    start_page_input = input("请输入起始页数（默认0）: ").strip()
    try:
        start_page = int(start_page_input) if start_page_input else 0
    except ValueError:
        print("输入无效，使用默认值0")
        start_page = 0
    
    current_page = start_page
    all_matches = []  # 存储所有匹配结果
    
    while True:
        # 3. 搜索当前页
        has_matches, next_page, matches = search_content(query, current_page)
        
        if has_matches is None:
            print("搜索失败，请检查网络连接或稍后重试")
            break
        
        # 保存匹配结果
        if matches:
            all_matches.extend(matches)
        
        # 4. 根据结果提示用户
        if has_matches:
            print(f"\n✓ 在第 {current_page} 页找到了匹配结果！")
            
            # 询问用户是否继续搜索
            choice = input("\n请选择操作: \n1. 继续搜索下一页\n2. 跳转到指定页数\n3. 显示所有结果\n4. 退出\n请选择 (1/2/3/4): ").strip()
            
            if choice == '1':
                current_page = next_page
            elif choice == '2':
                try:
                    target_page = int(input("请输入要跳转的页数: ").strip())
                    current_page = target_page
                except ValueError:
                    print("输入无效，继续下一页")
                    current_page = next_page
            elif choice == '3':
                if all_matches:
                    print(f"\n=== 所有匹配结果（共 {len(all_matches)} 条）===")
                    for match in all_matches:
                        print(f"{match['编号']}. {match['位置']}: {match['内容']}")
                else:
                    print("没有找到匹配结果")
            elif choice == '4':
                print("退出搜索")
                break
            else:
                print("无效选择，继续下一页")
                current_page = next_page
                
        else:
            print(f"\n✗ 在第 {current_page} 页没有找到匹配结果")
            
            # 询问用户是否继续
            choice = input(f"\n是否继续搜索下一页？当前将跳转到第 {next_page} 页 (y/n): ").strip().lower()
            if choice in ['y', 'yes', '是', '继续']:
                current_page = next_page
            else:
                # 让用户选择其他页数
                new_choice = input("是否跳转到指定页数？(y/n): ").strip().lower()
                if new_choice in ['y', 'yes', '是']:
                    try:
                        target_page = int(input("请输入要跳转的页数: ").strip())
                        current_page = target_page
                    except ValueError:
                        print("输入无效，退出搜索")
                        break
                else:
                    print("退出搜索")
                    break

if __name__ == "__main__":
    main()
