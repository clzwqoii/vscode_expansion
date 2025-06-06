#!/usr/bin/env python3
import requests
import sys
import os
from tqdm import tqdm  # 新增进度条依赖
import json
def fetch_extension_info(short_name):
    """通过Marketplace API自动获取扩展完整信息"""
    api_url = "https://marketplace.visualstudio.com/_apis/public/gallery/extensionquery"
    headers = {
        'Accept': 'application/json;api-version=7.1-preview.1',
        'Content-Type': 'application/json'
    }
    payload = {
        "filters": [{
            "criteria": [
                {"filterType": 7, "value": short_name},
                {"filterType": 12, "value": "4096"}  # 搜索目标为扩展名称
            ],
            "pageNumber": 1,
            "pageSize": 1,
        }],
        "flags": 1039  # 获取完整信息的标志位
    }
    
    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            results = response.json()
           
            if results['results'] and results['results'][0]['extensions']:
                extension = results['results'][0]['extensions'][0]
                # 新增下载URL提取
                download_url = f"https://marketplace.visualstudio.com/_apis/public/gallery/publishers/{extension['publisher']['publisherName']}/vsextensions/{extension['extensionName']}/{extension['versions'][0]['version']}/vspackage"
                 
                try:
                    return {
                        'name': f"{extension['publisher']['publisherName']}.{extension['extensionName']}",
                        'download_url': download_url,
                        'latest_version': extension['versions'][0]['version']
                    }
                except KeyError as e:
                    print(f"API返回数据结构不完整: {e}")
                    return None
    except Exception as e:
        print(f"API查询失败: {e}")
    return None

def get_latest_version(item_name):
    """获取扩展最新版本信息"""
    url = f"https://marketplace.visualstudio.com/items?itemName={item_name}&ssr=false"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            # 简单解析页面获取版本信息（实际需要更精确的解析）
            if 'data-extension-version' in response.text:
                return response.text.split('data-extension-version="')[1].split('"')[0]
    except Exception as e:
        print(f"获取版本失败: {e}")
    return None

def download_extension(download_url, filename):
    """下载指定扩展"""
    # 检查文件是否存在
    filepath = os.path.join(os.getcwd(), filename)
    if os.path.exists(filepath):
        print(f"插件 {filename} 已存在，跳过本次下载")
        return None
    
    try:
        print(f"正在下载: {filename}")
        response = requests.get(download_url, stream=True, timeout=30)
        if response.status_code == 200:
            # 添加下载进度条
            total_size = int(response.headers.get('content-length', 0))
            progress_bar = tqdm(total=total_size, unit='B', unit_scale=True, desc=filename)
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        progress_bar.update(len(chunk))
            progress_bar.close()
            print(f"\n下载完成: {filename}")
            return filepath
        else:
            print(f"下载失败，HTTP状态码: {response.status_code}")
    except Exception as e:
        print(f"下载异常: {e}")
    return None

if __name__ == "__main__":

    # 支持混合格式的插件列表
    item_names = [
        # 'ms-python.python',          # 简写形式（自动转换）
        # 'ms-python.debugpy',
        # 'ms-azuretools.vscode-docker',          # 简写形式（自动转换）
        # 'HookyQR.minify',
        # 'xdebug.php-debug',
        # 'bmewburn.vscode-intelephense-client',
        'ms-python.black-formatter'
    ]
    
    for item_name in item_names:
        original_name = item_name = item_name.strip()
        if not item_name:
            continue
            
        # 初始化变量
        download_url = None
        filename = None
        
        
        # 完整名称处理
        extension_info = fetch_extension_info(item_name)
        
        if extension_info:
            download_url = extension_info['download_url']
            filename = f"{item_name}-{extension_info['latest_version']}.vsix"
        else:
            print(f"\n无法获取扩展信息: {item_name}")
            continue
                
        # 确保filename已定义
        if not filename or not download_url:
            print(f"\n无法获取下载信息: {original_name}")
            continue

        # 新增提前检查文件逻辑
        filepath = os.path.join(os.getcwd(), filename)
        if os.path.exists(filepath):
            print(f"\n插件 {filename} 已存在，跳过下载")
            continue  # 立即跳过当前循环

        # 构造下载URL用于提示
        print(f"\n准备下载 {filename}\n链接: {download_url}")
        confirm = input("按回车确认下载，输入no跳过当前下载: ")
        if confirm.lower() == 'no':
            print("跳过当前下载")
            continue
        
        # 执行下载并等待完成
        download_result = download_extension(download_url, filename)
    
        # 新增下载完成确认逻辑
        if download_result:
            print(f"已完成 {filename} 下载，开始处理下一个插件...")
        else:
            print(f"下载失败，跳过后续处理")