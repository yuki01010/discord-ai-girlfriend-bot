# 💬 AIトークBot テンプレート（Discord + OpenAI）

Discord上で動作する「記憶つき・雰囲気自動切替」型のAIキャラBotテンプレートです。  
スラッシュコマンドで簡単操作、**名前 / 好み / メモ** を学習して会話がどんどん進化します。

---

## 🚀 主な機能
- `/talk` … 記憶＋人格プロンプトでの会話
- `/memory_show` … 長期記憶の閲覧
- `/memory_set_name` … 呼び名を登録（例：あなた、君、ニックネームなど）
- `/memory_add_like` … 好きな話題を追加入力（例：ラーメン）
- `/memory_add_note` … メモを1行追加
- `/memory_clear` … 記憶リセット（任意で追加可能）
- `/vibe_on` / `/vibe_off` … 雰囲気自動切替のON/OFF（任意で追加可能）

---

## 🧠 会話の特徴
- OpenAI APIを使用し、**性格・好み・メモ・直近要約**を踏まえた一貫した会話を生成  
- 甘々／ツン／クール／励まし など、発話内容から自動で雰囲気切替  
- JSON形式で長期記憶を永続保存（`memory_db.json`）  
- `.env`による安全な秘密管理（APIキーや設定をコードに含めない）

---

## 🧩 必要なもの
- Python 3.10 以上
- Discord Bot Token（[Discord Developer Portal](https://discord.com/developers/applications)で発行）
- OpenAI API Key（有料アカウント推奨）

---

## ⚙️ セットアップ

```bash
# リポジトリを取得
git clone https://github.com/<yourname>/discord-ai-girlfriend-bot.git

# フォルダに移動
cd discord-ai-girlfriend-bot

# 依存ライブラリをインストール
pip install -r requirements.txt

## 📜 ライセンス
MIT License  
このテンプレートはMITライセンスのもとで配布されています。  
改変・再配布・商用利用は自由ですが、LICENSEファイルを残してください。  

