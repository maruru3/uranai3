"""uranai3 — 毎日の星座動画生成ワークフロー
Playwright MCP 経由で sora.com を操作する。

使い方:
  Claude Code から以下のように実行:
    python uranai3/run_daily.py

  または Claude に直接:
    「uranai3の今日の動画を作って」
"""
import json
import logging
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent
PROMPTS_DIR = BASE_DIR / "prompts"
RESULTS_DIR = BASE_DIR / "results"


def load_today_prompts() -> list[dict]:
    """今日のプロンプトを読み込み（なければ生成）"""
    jst = timezone(timedelta(hours=9))
    today = datetime.now(jst).date().isoformat()

    prompt_file = PROMPTS_DIR / f"{today}_prompts.json"

    if not prompt_file.exists():
        logger.info("Prompts not found, generating...")
        from fetch_and_prompt import run
        run("ja")

    if prompt_file.exists():
        data = json.loads(prompt_file.read_text(encoding="utf-8"))
        logger.info(f"Loaded {len(data)} prompts for {today}")
        return data
    else:
        logger.error("Failed to generate prompts")
        return []


def save_result(date: str, results: list[dict]) -> Path:
    """結果をJSONに保存"""
    RESULTS_DIR.mkdir(exist_ok=True)
    output_file = RESULTS_DIR / f"{date}_videos.json"
    output_file.write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    logger.info(f"Results saved to {output_file}")
    return output_file


def print_instructions(prompts: list[dict]) -> None:
    """Claudeへの指示を表示"""
    jst = timezone(timedelta(hours=9))
    today = datetime.now(jst).date().isoformat()

    print("\n" + "=" * 60)
    print(f"  uranai3 Daily Video Generation ({today})")
    print("=" * 60)
    print(f"\n  {len(prompts)} videos to generate:\n")

    for p in prompts:
        print(f"  #{p['rank']} {p['sign'].upper()} - {p['comment']}")

    print("\n" + "-" * 60)
    print("  Claude への指示（コピペ用）:")
    print("-" * 60)
    print("""
  以下の手順で sora.com で動画を生成してください:

  1. sora.com の Explore ページを開く
  2. 各プロンプトについて:
     a. テキストボックスにプロンプトを入力
     b. 「Create video」をクリック
     c. 次のプロンプトへ
  3. Drafts ページで生成完了を待つ（約1-2分/本）
  4. 各動画の「...」→「Copy link」でリンク取得
  5. リンクをまとめて results/ に保存
""")

    print("  プロンプト一覧:")
    print("-" * 60)
    for i, p in enumerate(prompts):
        print(f"\n  [{i+1}/{len(prompts)}] #{p['rank']} {p['sign'].upper()}")
        print(f"  {p['sora_prompt']}")

    print("\n" + "=" * 60)


# ── Playwright MCP 用ヘルパー関数 ──
# これらは Claude が Playwright MCP ツールで使用するための
# ステップバイステップガイド

PLAYWRIGHT_STEPS = """
=== Playwright MCP 自動化ステップ ===

Step 1: sora.com を開く
  → browser_navigate("https://sora.chatgpt.com/explore")

Step 2: 各プロンプトを投入 (3回繰り返し)
  → browser_click(textbox "Describe your video...")
  → browser_fill_form(textbox, prompt_text)
  → browser_click(button "Create video")
  → 待機 5秒

Step 3: Drafts で完了を確認
  → browser_navigate("https://sora.chatgpt.com/drafts")
  → 60秒待機
  → browser_take_screenshot() で確認
  → ローディングスピナーが消えるまで繰り返し

Step 4: 各動画のリンクを取得
  → 動画をクリック
  → ... メニュー → "Copy link" → 確認ダイアログで "Copy link"
  → URL をメモ (/p/s_xxx 形式)

Step 5: 結果保存
  → results/{date}_videos.json に保存
"""


if __name__ == "__main__":
    prompts = load_today_prompts()
    if not prompts:
        print("ERROR: No prompts available")
        sys.exit(1)

    print_instructions(prompts)
    print(PLAYWRIGHT_STEPS)
