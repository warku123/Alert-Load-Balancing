#!/usr/bin/env python3
"""
测试 webhook 端点脚本
使用 webhook_payload_example.json 作为测试数据
"""
import json
import sys
from pathlib import Path
import requests

# 获取脚本所在目录
SCRIPT_DIR = Path(__file__).parent
PAYLOAD_FILE = SCRIPT_DIR / "webhook_payload_example.json"
WEBHOOK_URL = "http://localhost:8048/webhook"


def test_webhook():
    # 读取测试数据
    if not PAYLOAD_FILE.exists():
        print(f"❌ 错误: 找不到测试文件 {PAYLOAD_FILE}")
        sys.exit(1)
    
    try:
        with open(PAYLOAD_FILE, 'r', encoding='utf-8') as f:
            payload = json.load(f)
        print(f"✓ 已加载测试数据: {PAYLOAD_FILE}")
    except json.JSONDecodeError as e:
        print(f"❌ 错误: JSON 解析失败 - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 错误: 读取文件失败 - {e}")
        sys.exit(1)
    
    # 显示测试数据摘要
    print(f"\n测试数据摘要:")
    print(f"  - 接收者: {payload.get('receiver', 'N/A')}")
    print(f"  - 状态: {payload.get('status', 'N/A')}")
    print(f"  - 报警数量: {len(payload.get('alerts', []))}")
    print(f"  - 标题: {payload.get('title', 'N/A')}")
    
    # 发送请求
    print(f"\n正在发送请求到: {WEBHOOK_URL}")
    
    try:
        response = requests.post(
            WEBHOOK_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        # 显示响应结果
        print(f"HTTP 状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        print(f"\n响应内容:")
        
        try:
            response_json = response.json()
            print(json.dumps(response_json, ensure_ascii=False, indent=2))
        except json.JSONDecodeError:
            print(response.text)
            response_json = None
        
        # 判断结果
        print("\n" + "=" * 60)
        if response.status_code == 200:
            print("✓ 测试成功！请求已接收")
            if isinstance(response_json, dict) and response_json.get("success"):
                provider = response_json.get("provider")
                if provider:
                    print(f"  - 转发到提供者: {provider}")
                else:
                    print("  - 仅记录在本地日志（无可用提供者）")
        else:
            print(f"⚠️  测试返回状态码: {response.status_code}")
        
        return response.status_code == 200
        
    except requests.exceptions.ConnectionError:
        print(f"❌ 错误: 无法连接到 {WEBHOOK_URL}")
        print("   请确保服务正在运行在端口 8048")
        sys.exit(1)
    except requests.exceptions.Timeout:
        print("❌ 错误: 请求超时")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    test_webhook()

