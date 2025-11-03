# 可愛い彼女Bot（Discord + OpenAI）

Discord上で動く「記憶つき・雰囲気自動切替」彼女Botのテンプレです。  
スラッシュコマンドで簡単操作、**名前/好み/メモ**を学習して会話がどんどん馴染みます。

## 機能
- `/talk` … 記憶＋人格プロンプトで会話
- `/memory_show` … 長期記憶の閲覧
- `/memory_set_name` … 呼び名を登録（例: ゆうきくん）
- `/memory_add_like` … 好みを追加入力（例: ラーメン）
- `/memory_add_note` … メモを1行追加
- `/memory_clear` … 記憶リセット
- `/vibe_on` / `/vibe_off` … 会話の雰囲気 自動切替ON/OFF

## 必要なもの
- Python 3.10 以上
- Discord Bot（Token）
- OpenAI API Key（課金アカウント）

## セットアップ

```bash
git clone https://github.com/<yourname>/discord-ai-girlfriend-bot.git
cd discord-ai-girlfriend-bot
pip install -r requirements.txt
