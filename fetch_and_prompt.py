"""uranai3 — 12星座Sora動画プロンプト生成
全12星座のSora動画生成プロンプトを作成する。
"""
import json
import logging
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "prompts"

# 星座ごとのビジュアルテーマ（Soraプロンプト用）
ZODIAC_VISUALS: dict[str, dict[str, str]] = {
    "aries": {
        "symbol": "ram",
        "zodiac_glyph": "the Aries zodiac glyph (two curved horns symbol)",
        "element": "fire",
        "color": "crimson red and gold",
        "scene": "a majestic ram standing on a volcanic mountain peak at sunrise, flames dancing around its golden horns",
        "mood": "powerful, energetic, bold",
    },
    "taurus": {
        "symbol": "bull",
        "zodiac_glyph": "the Taurus zodiac glyph (a circle with horns symbol)",
        "element": "earth",
        "color": "emerald green and bronze",
        "scene": "a noble bull resting in a lush flower garden with cherry blossoms falling, golden light filtering through trees",
        "mood": "serene, luxurious, grounded",
    },
    "gemini": {
        "symbol": "twins",
        "zodiac_glyph": "the Gemini zodiac glyph (two vertical lines symbol)",
        "element": "air",
        "color": "bright yellow and silver",
        "scene": "twin ethereal figures dancing among floating books and glowing butterflies in a starlit sky",
        "mood": "playful, intellectual, dynamic",
    },
    "cancer": {
        "symbol": "crab",
        "zodiac_glyph": "the Cancer zodiac glyph (two curved shapes symbol)",
        "element": "water",
        "color": "pearl white and moonlit silver",
        "scene": "a luminous crab on a moonlit beach with gentle waves, the full moon reflecting on the ocean surface",
        "mood": "nurturing, mystical, gentle",
    },
    "leo": {
        "symbol": "lion",
        "zodiac_glyph": "the Leo zodiac glyph (a curved lion tail symbol)",
        "element": "fire",
        "color": "royal gold and orange",
        "scene": "a magnificent lion with a golden mane standing proudly on a sunlit savanna, sun rays creating a crown of light",
        "mood": "regal, confident, radiant",
    },
    "virgo": {
        "symbol": "maiden",
        "zodiac_glyph": "the Virgo zodiac glyph (an M with a loop symbol)",
        "element": "earth",
        "color": "soft green and lavender",
        "scene": "an elegant maiden in a wheat field holding a glowing crystal, surrounded by healing herbs and butterflies",
        "mood": "graceful, pure, meticulous",
    },
    "libra": {
        "symbol": "scales",
        "zodiac_glyph": "the Libra zodiac glyph (balanced scales symbol)",
        "element": "air",
        "color": "pastel pink and sky blue",
        "scene": "golden balance scales floating in a rose garden with rainbow light beams, petals swirling in harmony",
        "mood": "harmonious, elegant, balanced",
    },
    "scorpio": {
        "symbol": "scorpion",
        "zodiac_glyph": "the Scorpio zodiac glyph (an M with an arrow tail symbol)",
        "element": "water",
        "color": "deep crimson and black",
        "scene": "a mystical scorpion with glowing ruby eyes emerging from dark waters under a blood-red nebula sky",
        "mood": "intense, mysterious, transformative",
    },
    "sagittarius": {
        "symbol": "archer",
        "zodiac_glyph": "the Sagittarius zodiac glyph (an arrow pointing up-right symbol)",
        "element": "fire",
        "color": "royal purple and indigo",
        "scene": "a centaur archer shooting a flaming arrow across a vast galaxy, stars exploding into constellations",
        "mood": "adventurous, free, philosophical",
    },
    "capricorn": {
        "symbol": "sea-goat",
        "zodiac_glyph": "the Capricorn zodiac glyph (a V with a curved tail symbol)",
        "element": "earth",
        "color": "dark brown and charcoal",
        "scene": "a determined mountain goat climbing a snowy peak at dawn, reaching the summit as golden light breaks through clouds",
        "mood": "ambitious, disciplined, triumphant",
    },
    "aquarius": {
        "symbol": "water-bearer",
        "zodiac_glyph": "the Aquarius zodiac glyph (two wavy lines symbol)",
        "element": "air",
        "color": "electric blue and turquoise",
        "scene": "an ethereal figure pouring luminous water that transforms into lightning and digital streams across a futuristic cityscape",
        "mood": "innovative, visionary, revolutionary",
    },
    "pisces": {
        "symbol": "fish",
        "zodiac_glyph": "the Pisces zodiac glyph (two curved lines tied together symbol)",
        "element": "water",
        "color": "ocean blue and iridescent violet",
        "scene": "two koi fish swimming in a circle through an underwater galaxy, surrounded by bioluminescent coral and aurora light",
        "mood": "dreamy, spiritual, enchanting",
    },
}

# 星座の順番（牡羊座〜魚座）
ZODIAC_ORDER = [
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
]


def generate_sora_prompt(sign: str) -> str:
    """星座に応じたSora動画生成プロンプトを作成"""
    visual = ZODIAC_VISUALS[sign]

    prompt = (
        f"Create a stunning 10-second zodiac horoscope video. "
        f"Scene: {visual['scene']}. "
        f"In the sky above, a large glowing {visual['zodiac_glyph']} "
        f"shines as a celestial emblem. "
        f"Color palette: {visual['color']}. "
        f"Mood: {visual['mood']}. "
        f"Visual effects: gentle sparkles and radiant light particles floating, "
        f"soft celestial glow surrounding the scene. "
        f"Style: cinematic, ethereal, anime-inspired celestial art. "
        f"Camera: slow dramatic zoom with gentle orbit."
    )
    return prompt


def run() -> list[dict]:
    """メイン処理: 12星座のプロンプト生成"""
    jst = timezone(timedelta(hours=9))
    target_date = datetime.now(jst).date().isoformat()
    logger.info(f"Date: {target_date}")

    results = []
    for sign in ZODIAC_ORDER:
        prompt = generate_sora_prompt(sign)
        result = {
            "sign": sign,
            "sora_prompt": prompt,
            "date": target_date,
        }
        results.append(result)
        logger.info(f"{sign}: prompt generated ({len(prompt)} chars)")

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
    print(f"  12 Zodiac Signs Sora Prompts ({target_date})")
    print("=" * 60)
    for r in results:
        print(f"\n  {r['sign'].upper()}")
        print(f"  Sora Prompt ({len(r['sora_prompt'])} chars):")
        print(f"  {r['sora_prompt'][:100]}...")
    print("\n" + "=" * 60)

    return results


if __name__ == "__main__":
    run()
