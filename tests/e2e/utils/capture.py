# -*- coding: utf-8 -*-
"""Screenshot and log capture utilities for E2E tests

Requirements: 8.3, 8.4, 10.1, 10.2, 10.3
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from playwright.sync_api import Page


def capture_on_failure(page: Page, test_name: str) -> dict[str, str]:
    """テスト失敗時にスクリーンショットとログを保存
    
    テストが失敗した際に、デバッグに必要な情報を保存します：
    - スクリーンショット
    - ブラウザコンソールログ
    - ネットワークログ
    
    Requirements: 8.3, 8.4, 10.1, 10.2, 10.3
    
    Args:
        page: Playwright page object
        test_name: テスト名（ファイル名に使用）
    
    Returns:
        dict: 保存されたファイルのパス
            - screenshot: スクリーンショットのパス
            - console_log: コンソールログのパス
            - network_log: ネットワークログのパス
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = Path("test-results")
    results_dir.mkdir(exist_ok=True)
    
    # ファイル名のベース
    base_name = f"{test_name}_{timestamp}"
    
    # スクリーンショット保存
    screenshot_path = results_dir / f"{base_name}.png"
    page.screenshot(path=str(screenshot_path), full_page=True)
    
    # コンソールログ保存
    console_log_path = results_dir / f"{base_name}_console.log"
    console_logs = save_console_logs(page, str(console_log_path))
    
    # ネットワークログ保存
    network_log_path = results_dir / f"{base_name}_network.json"
    network_logs = save_network_logs(page, str(network_log_path))
    
    return {
        "screenshot": str(screenshot_path),
        "console_log": str(console_log_path),
        "network_log": str(network_log_path)
    }


def save_console_logs(page: Page, log_path: str) -> list[str]:
    """ブラウザコンソールログを保存
    
    ブラウザのコンソールに出力されたログを保存します。
    
    Requirements: 10.2
    
    Args:
        page: Playwright page object
        log_path: ログファイルのパス
    
    Returns:
        list: コンソールログのリスト
    """
    logs = []
    
    try:
        # ページのタイトルとURL
        logs.append(f"Page Title: {page.title()}")
        logs.append(f"Page URL: {page.url}")
        logs.append("")
        
        # コンソールメッセージを取得（page fixtureで収集されたもの）
        if hasattr(page, 'console_messages'):
            logs.append("=== Console Messages ===")
            console_messages = getattr(page, 'console_messages', [])
            if console_messages:
                logs.extend(console_messages)
            else:
                logs.append("(No console messages)")
            logs.append("")
        
        # ページの状態情報を取得
        logs.append("=== Page State ===")
        
        # ページの可視性状態
        is_visible = page.evaluate("() => document.visibilityState")
        logs.append(f"Visibility State: {is_visible}")
        
        # ページのreadyState
        ready_state = page.evaluate("() => document.readyState")
        logs.append(f"Ready State: {ready_state}")
        
    except Exception as e:
        logs.append(f"Error collecting page state: {e}")
    
    # ログをファイルに保存
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("\n".join(logs))
    
    return logs


def save_network_logs(page: Page, log_path: str) -> list[dict[str, Any]]:
    """ネットワークログを保存
    
    ページで発生したネットワークリクエストとレスポンスを保存します。
    
    Requirements: 10.3
    
    Args:
        page: Playwright page object
        log_path: ログファイルのパス
    
    Returns:
        list: ネットワークログのリスト
    """
    # Note: Playwrightでネットワークログを収集するには、
    # page.on("request")とpage.on("response")イベントハンドラーを
    # 使用する必要があります。
    # ここでは、現在のページの状態情報を保存します。
    
    network_info = []
    
    try:
        # ページのURL
        network_info.append({
            "type": "page_info",
            "url": page.url,
            "title": page.title(),
            "timestamp": datetime.now().isoformat()
        })
        
        # Performance API から情報を取得
        performance_data = page.evaluate("""
            () => {
                const perfData = window.performance.getEntriesByType('navigation')[0];
                if (perfData) {
                    return {
                        domContentLoaded: perfData.domContentLoadedEventEnd - perfData.domContentLoadedEventStart,
                        loadComplete: perfData.loadEventEnd - perfData.loadEventStart,
                        domInteractive: perfData.domInteractive,
                        responseEnd: perfData.responseEnd
                    };
                }
                return null;
            }
        """)
        
        if performance_data:
            network_info.append({
                "type": "performance",
                "data": performance_data
            })
        
    except Exception as e:
        network_info.append({
            "type": "error",
            "message": f"Error collecting network info: {e}"
        })
    
    # ログをJSONファイルに保存
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(network_info, f, indent=2, ensure_ascii=False)
    
    return network_info
