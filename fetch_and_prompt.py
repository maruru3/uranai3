"""uranai3 — Step 1 & 2: ランキング取得 + Sora用プロンプト自動生成
uranai2 APIから今日の1〜3位を取得し、各星座にマッチした
Sora動画生成プロンプトを作成する。
"""
import json
import logging
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "prompts"

# uranai2 のURL（Render本番）
URANAI2_URL = "https://fortune-teller-hxyq.onrender.com"

# 星座ごとのビジュアルテーマ（Soraプロンプト用）
ZODIAC_VISUALS: dict[str, dict[str, str]] = {
    "aries": {
        "symbol": "ram",
        "zodiac_glyph": "the Aries zodiac glyph (♈, two curved horns)",
        "element": "fire",
        "color": "crimson red and gold",
        "scene": "a majestic ram standing on a volcanic mountain peak at sunrise, flames dancing around its golden horns",
        "mood": "powerful, energetic, bold",
    },
    "taurus": {
        "symbol": "bull",
        "zodiac_glyph": "the Taurus zodiac glyph (♉, a circle with horns)",
        "element": "earth",
        "color": "emerald green and bronze",
        "scene": "a noble bull resting in a lush flower garden with cherry blossoms falling, golden light filtering through trees",
        "mood": "serene, luxurious, grounded",
    },
    "gemini": {
        "symbol": "twins",
        "zodiac_glyph": "the Gemini zodiac glyph (♊, two vertical lines)",
        "element": "air",
        "color": "bright yellow and silver",
        "scene": "twin ethereal figures dancing among floating books and glowing butterflies in a starlit sky",
        "mood": "playful, intellectual, dynamic",
    },
    "cancer": {
        "symbol": "crab",
        "zodiac_glyph": "the Cancer zodiac glyph (♋, two curved shapes)",
        "element": "water",
        "color": "pearl white and moonlit silver",
        "scene": "a luminous crab on a moonlit beach with gentle waves, the full moon reflecting on the ocean surface",
        "mood": "nurturing, mystical, gentle",
    },
    "leo": {
        "symbol": "lion",
        "zodiac_glyph": "the Leo zodiac glyph (♌, a curved lion tail)",
        "element": "fire",
        "color": "royal gold and orange",
        "scene": "a magnificent lion with a golden mane standing proudly on a sunlit savanna, sun rays creating a crown of light",
        "mood": "regal, confident, radiant",
    },
    "virgo": {
        "symbol": "maiden",
        "zodiac_glyph": "the Virgo zodiac glyph (♍, an M with a loop)",
        "element": "earth",
        "color": "soft green and lavender",
        "scene": "an elegant maiden in a wheat field holding a glowing crystal, surrounded by healing herbs and butterflies",
        "mood": "graceful, pure, meticulous",
    },
    "libra": {
        "symbol": "scales",
        "zodiac_glyph": "the Libra zodiac glyph (♎, balanced scales)",
        "element": "air",
        "color": "pastel pink and sky blue",
        "scene": "golden balance scales floating in a rose garden with rainbow light beams, petals swirling in harmony",
        "mood": "harmonious, elegant, balanced",
    },
    "scorpio": {
        "symbol": "scorpion",
        "zodiac_glyph": "the Scorpio zodiac glyph (♏, an M with an arrow tail)",
        "element": "water",
        "color": "deep crimson and black",
        "scene": "a mystical scorpion with glowing ruby eyes emerging from dark waters under a blood-red nebula sky",
        "mood": "intense, mysterious, transformative",
    },
    "sagittarius": {
        "symbol": "archer",
        "zodiac_glyph": "the Sagittarius zodiac glyph (♐, an arrow pointing up-right)",
        "element": "fire",
        "color": "royal purple and indigo",
        "scene": "a centaur archer shooting a flaming arrow across a vast galaxy, stars exploding into constellations",
        "mood": "adventurous, free, philosophical",
    },
    "capricorn": {
        "symbol": "sea-goat",
        "zodiac_glyph": "the Capricorn zodiac glyph (♑, a V with a curved tail)",
        "element": "earth",
        "color": "dark brown and charcoal",
        "scene": "a determined mountain goat climbing a snowy peak at dawn, reaching the summit as golden light breaks through clouds",
        "mood": "ambitious, disciplined, triumphant",
    },
    "aquarius": {
        "symbol": "water-bearer",
        "zodiac_glyph": "the Aquarius zodiac glyph (♒, two wavy lines)",
        "element": "air",
        "color": "electric blue and turquoise",
        "scene": "an ethereal figure pouring luminous water that transforms into lightning and digital streams across a futuristic cityscape",
        "mood": "innovative, visionary, revolutionary",
    },
    "pisces": {
        "symbol": "fish",
        "zodiac_glyph": "the Pisces zodiac glyph (♓, two curved lines tied together)",
        "element": "water",
        "color": "ocean blue and iridescent violet",
        "scene": "two koi fish swimming in a circle through an underwater galaxy, surrounded by bioluminescent coral and aurora light",
        "mood": "dreamy, spiritual, enchanting",
    },
}

# ランク別の演出テーマ
RANK_THEMES: dict[int, dict[str, str]] = {
    1: {
        "effect": "golden sparkles and radiant light particles gently floating upward, warm golden glow surrounding the scene",
        "text_overlay": "1st",
        "text_desc": 'A large glowing golden text "1st" prominently displayed at the top center of the frame.',
        "energy": "triumphant, majestic, radiant warmth",
    },
    2: {
        "effect": "soft silver shimmer particles and elegant light beams, gentle stardust falling",
        "text_overlay": "2nd",
        "text_desc": 'A large glowing silver text "2nd" prominently displayed at the top center of the frame.',
        "energy": "graceful, confident glow, beautiful radiance",
    },
    3: {
        "effect": "warm bronze sparkles and soft candlelight glow, gentle ember particles drifting",
        "text_overlay": "3rd",
        "text_desc": 'A large glowing bronze text "3rd" prominently displayed at the top center of the frame.',
        "energy": "warm, hopeful, gentle encouragement",
    },
}


def fetch_today_ranking(lang: str = "ja") -> dict:
    """uranai2 APIから今日のランキングを取得"""
    url = f"{URANAI2_URL}/api/today?lang={lang}"
    logger.info(f"Fetching ranking from {url}")
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.json()


def get_top3(ranking_data: dict) -> list[dict]:
    """ランキングデータから1〜3位を抽出"""
    ranking = ranking_data.get("ranking", [])
    return [item for item in ranking if item["rank"] <= 3]


def generate_sora_prompt(sign: str, rank: int, comment: str, lucky_item: str) -> str:
    """星座+順位に応じたSora動画生成プロンプトを作成"""
    visual = ZODIAC_VISUALS.get(sign, ZODIAC_VISUALS["aries"])
    theme = RANK_THEMES.get(rank, RANK_THEMES[3])

    prompt = (
        f"Create a stunning 10-second zodiac horoscope video. "
        f"Scene: {visual['scene']}. "
        f"In the sky above, a large glowing {visual['zodiac_glyph']} "
        f"shines as a celestial emblem. "
        f"{theme['text_desc']} "
        f"Color palette: {visual['color']}. "
        f"Mood: {visual['mood']}. "
        f"Visual effects: {theme['effect']}. "
        f"The atmosphere should convey {theme['energy']}. "
        f"Style: cinematic, ethereal, anime-inspired celestial art. "
        f"Camera: slow dramatic zoom with gentle orbit."
    )
    return prompt


def run(lang: str = "ja") -> list[dict]:
    """メイン処理: ランキング取得 → プロンプト生成"""
    # Step 1: ランキング取得
    try:
        ranking_data = fetch_today_ranking(lang)
    except requests.RequestException as e:
        logger.error(f"Failed to fetch ranking: {e}")
        logger.info("Using sample data for testing")
        ranking_data = _sample_ranking()

    target_date = ranking_data.get("date", "unknown")
    logger.info(f"Date: {target_date}")

    # Step 2: Top 3 抽出 + プロンプト生成
    top3 = get_top3(ranking_data)
    results = []

    for item in top3:
        rank = item["rank"]
        sign = item["sign"]
        comment = item.get("comment", "")
        lucky_item = item.get("lucky_item", "")

        prompt = generate_sora_prompt(sign, rank, comment, lucky_item)

        result = {
            "rank": rank,
            "sign": sign,
            "comment": comment,
            "lucky_item": lucky_item,
            "sora_prompt": prompt,
            "date": target_date,
        }
        results.append(result)
        logger.info(f"#{rank} {sign}: prompt generated ({len(prompt)} chars)")

    # 出力保存
    OUTPUT_DIR.mkdir(exist_ok=True)
    output_file = OUTPUT_DIR / f"{target_date}_prompts.json"
    output_file.write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    logger.info(f"Saved to {output_file}")

    # 見やすく表示
    print("\n" + "=" * 60)
    print(f"  Today's Top 3 Zodiac Signs ({target_date})")
    print("=" * 60)
    for r in results:
        print(f"\n  #{r['rank']} {r['sign'].upper()}")
        print(f"  Comment: {r['comment']}")
        print(f"  Lucky Item: {r['lucky_item']}")
        print(f"  Sora Prompt ({len(r['sora_prompt'])} chars):")
        print(f"  {r['sora_prompt'][:120]}...")
    print("\n" + "=" * 60)

    return results


def _sample_ranking() -> dict:
    """テスト用サンプルデータ"""
    jst = timezone(timedelta(hours=9))
    today = datetime.now(jst).date().isoformat()
    return {
        "date": today,
        "ranking": [
            {"rank": 1, "sign": "leo", "comment": "最高の一日！自信を持って進もう", "lucky_item": "ゴールドのアクセサリー"},
            {"rank": 2, "sign": "pisces", "comment": "直感が冴える日。心の声に従って", "lucky_item": "アクアマリン"},
            {"rank": 3, "sign": "aries", "comment": "行動力が光る！新しい挑戦に◎", "lucky_item": "赤いペン"},
            {"rank": 4, "sign": "gemini", "comment": "コミュニケーション運UP", "lucky_item": "手帳"},
            {"rank": 5, "sign": "libra", "comment": "バランスの良い日", "lucky_item": "花"},
            {"rank": 6, "sign": "sagittarius", "comment": "冒険心が吉", "lucky_item": "地図"},
            {"rank": 7, "sign": "aquarius", "comment": "独創的なアイデアが浮かぶ", "lucky_item": "ノート"},
            {"rank": 8, "sign": "taurus", "comment": "穏やかな日", "lucky_item": "ハーブティー"},
            {"rank": 9, "sign": "cancer", "comment": "家族との時間を大切に", "lucky_item": "写真"},
            {"rank": 10, "sign": "virgo", "comment": "細かい作業に集中", "lucky_item": "メガネ"},
            {"rank": 11, "sign": "capricorn", "comment": "着実に前進", "lucky_item": "時計"},
            {"rank": 12, "sign": "scorpio", "comment": "充電日。ゆっくり休もう", "lucky_item": "キャンドル"},
        ],
    }


if __name__ == "__main__":
    lang = sys.argv[1] if len(sys.argv) > 1 else "ja"
    run(lang)
