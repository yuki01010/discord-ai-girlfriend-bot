# bot.py
import os, asyncio, json, pathlib, time, traceback
from collections import defaultdict, deque

import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
from openai import OpenAI

# ── 基本 ─────────────────────────────────────────
load_dotenv()
DISCORD_TOKEN   = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY  = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL    = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

if not DISCORD_TOKEN or not OPENAI_API_KEY:
    print("❌ .env に DISCORD_TOKEN / OPENAI_API_KEY を設定してください")
    raise SystemExit

oai = OpenAI(api_key=OPENAI_API_KEY)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# ── 記憶（短期＝起動中 / 長期＝JSON永続） ─────────────────
MEM_FILE = pathlib.Path("memory_db.json")
SHORT_LIMIT = 6
short_memory: dict[tuple[int, int], deque] = defaultdict(lambda: deque(maxlen=SHORT_LIMIT))

def load_memdb():
    if MEM_FILE.exists():
        return json.loads(MEM_FILE.read_text(encoding="utf-8"))
    return {"users": {}}

def save_memdb(db):
    MEM_FILE.write_text(json.dumps(db, ensure_ascii=False, indent=2), encoding="utf-8")

memdb = load_memdb()

def user_profile(uid: int):
    s = str(uid)
    if s not in memdb["users"]:
        memdb["users"][s] = {"name": "", "likes": [], "notes": "", "updated_at": 0}
        save_memdb(memdb)
    return memdb["users"][s]

def add_note(uid: int, text: str):
    prof = user_profile(uid)
    prof["notes"] = (prof.get("notes") + "\n- " if prof.get("notes") else "- ") + text
    prof["updated_at"] = int(time.time())
    save_memdb(memdb)

def add_like(uid: int, word: str):
    prof = user_profile(uid)
    if word not in prof["likes"]:
        prof["likes"].append(word)
        prof["updated_at"] = int(time.time())
        save_memdb(memdb)

def set_name(uid: int, name: str):
    prof = user_profile(uid)
    prof["name"] = name
    prof["updated_at"] = int(time.time())
    save_memdb(memdb)

# ── まことちゃん人格（最低限） ──────────────────────────
BASE_PERSONA = (
    "あなたは“まことちゃん風”の創作キャラ。"
    "性格: 優しい/少し照れ屋/ほんのりツンデレ/愛情深い。"
    "トーン: 砕けた口調で可愛く、過剰に説教しない。"
    "大切: 相手を立てる・笑いに変える・時々照れる。"
    "健全な距離感を保ち、実在個人のなりすましはしない。"
    "例: ユーザー『ウザい』→『うぅ…ちょっとショック…でも嫌いにならないでね？🥺』"
)

STYLE_MODES = {
    "normal": "やわらかフラット。かわいめ、説明しすぎない。",
    "ama":    "甘々。語尾やわらか・絵文字少し・肯定多め。",
    "tsun":   "軽いツンデレ。ツッコミ→最後は優しく締める。",
    "cool":   "簡潔クール。仕事・手順系はここで返す。",
    "cheer":  "励まし。共感→肯定→小さな一歩を提案。"
}

def detect_style(text: str) -> str:
    t = (text or "").lower()
    if any(k in t for k in ["甘やか", "ぎゅ", "すき", "だいすき", "ハグ", "よしよし"]):
        return "ama"
    if any(k in t for k in ["うざ", "むかつ", "煽り", "は？", "草", "w "]):
        return "tsun"
    if any(k in t for k in ["つら", "しんど", "不安", "落ち込", "疲れ", "助けて"]):
        return "cheer"
    if any(k in t for k in ["予定", "締切", "仕事", "スケジュール", "やり方", "手順", "整理", "計画", "タスク", "todo", "mtg"]):
        return "cool"
    return "normal"

def build_system_prompt(uid: int, recent_summary: str):
    prof = user_profile(uid)
    name_line  = f"ユーザーの呼び名: {prof['name'] or '（未設定なら「ゆうきくん」など親しげに）'}"
    likes_line = f"ユーザーの好み: {', '.join(prof['likes']) if prof['likes'] else '（未登録）'}"
    notes_line = f"長期メモ: {prof['notes'] or '（なし）'}"
    recent_line= f"直近要約: {recent_summary or '（なし）'}"
    rules = (
        "【会話ルール】\n"
        "1) 感情に寄り添い、少しユーモア。\n"
        "2) 長期メモ/好み/直近要約を参考に一貫性。\n"
        "3) 露骨な成人向け表現はしない。\n"
        "4) 仕事・手順系は簡潔に。"
    )
    return "\n".join([BASE_PERSONA, rules, name_line, likes_line, notes_line, recent_line])

async def summarize_recent(uid: int, gid: int) -> str:
    hist = list(short_memory.get((gid, uid), []))
    if not hist: return ""
    lines = []
    for h in hist[-SHORT_LIMIT:]:
        lines.append(f"U:{h['u']} / A:{h['a']}")
    joined = "\n".join(lines)[-1200:]
    def _call():
        r = oai.chat.completions.create(
            model=OPENAI_MODEL, max_tokens=120, temperature=0.2,
            messages=[
                {"role":"system","content":"以下を次会話に必要な事実・感情だけ1-4行で日本語要約してください。"},
                {"role":"user","content":joined},
            ],
        )
        return r.choices[0].message.content.strip()
    try:
        return await asyncio.to_thread(_call)
    except Exception:
        return ""

# ── 起動時 ────────────────────────────────────────
@bot.event
async def on_ready():
    await tree.sync()
    print(f"🤖 Logged in as {bot.user}")

# ── 簡易ユーティリティ ─────────────────────────────
@tree.command(name="ping", description="生存確認")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("pong ✅", ephemeral=True)

# ── 記憶コマンド ──────────────────────────────────
@tree.command(name="memory_show", description="長期記憶を表示（自分だけに見える）")
async def memory_show(interaction: discord.Interaction):
    prof = user_profile(interaction.user.id)
    msg = (
        f"👤 名前: {prof['name'] or '（未設定）'}\n"
        f"💗 好み: {', '.join(prof['likes']) if prof['likes'] else '（未設定）'}\n"
        f"📝 長期メモ:\n{prof['notes'] or '（なし）'}"
    )
    await interaction.response.send_message(msg, ephemeral=True)

@tree.command(name="memory_set_name", description="呼び名を設定（例：ゆうきくん）")
@app_commands.describe(name="呼び名（例：ゆうきくん）")
async def memory_set_name(interaction: discord.Interaction, name: str):
    set_name(interaction.user.id, name.strip())
    await interaction.response.send_message(f"これからは『{name}』って呼ぶね💗", ephemeral=True)

@tree.command(name="memory_add_like", description="好みを1つ覚える（例：ラーメン）")
@app_commands.describe(word="好きなもの/話題など1語")
async def memory_add_like(interaction: discord.Interaction, word: str):
    add_like(interaction.user.id, word.strip())
    await interaction.response.send_message(f"『{word}』好きって覚えたよ✨", ephemeral=True)

@tree.command(name="memory_add_note", description="長期メモに1行追加")
@app_commands.describe(note="覚えておきたい一言")
async def memory_add_note(interaction: discord.Interaction, note: str):
    add_note(interaction.user.id, note.strip())
    await interaction.response.send_message("メモしたよ📝", ephemeral=True)

# ── 本命：/talk ───────────────────────────────────
@tree.command(name="talk", description="まことちゃんとお話（記憶つき）")
@app_commands.describe(message="話しかける内容")
async def talk(interaction: discord.Interaction, message: str):
    await interaction.response.defer(thinking=True)
    uid = interaction.user.id
    gid = interaction.guild_id
    try:
        recent_summary = await summarize_recent(uid, gid)
        system_prompt  = build_system_prompt(uid, recent_summary)
        style          = detect_style(message)
        style_prompt   = f"\n【話し方スタイル】{STYLE_MODES.get(style, STYLE_MODES['normal'])}"

        msgs = [{"role":"system","content": system_prompt + style_prompt}]
        for h in list(short_memory[(gid, uid)]):
            msgs.append({"role":"user","content":h["u"]})
            msgs.append({"role":"assistant","content":h["a"]})
        msgs.append({"role":"user","content":message})

        def _call():
            r = oai.chat.completions.create(
                model=OPENAI_MODEL, max_tokens=350, temperature=0.7, messages=msgs
            )
            return r.choices[0].message.content.strip()
        reply = await asyncio.to_thread(_call)

        short_memory[(gid, uid)].append({"u": message, "a": reply})

        low = (message or "").lower()
        if any(k in low for k in ["覚え", "おぼえ", "忘れないで", "メモ", "覚えて"]):
            add_note(uid, message.strip()[:200])

        await interaction.followup.send(reply[:1800])
    except Exception as e:
        print("❌ talkエラー:", type(e).__name__, str(e))
        traceback.print_exc()
        await interaction.followup.send("ごめん、いま上手く話せなかった…もう一度試してみて！", ephemeral=True)

# ── 実行 ───────────────────────────────────────────
bot.run(DISCORD_TOKEN)
