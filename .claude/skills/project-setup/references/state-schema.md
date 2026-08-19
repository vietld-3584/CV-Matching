# `.setup-state.json` スキーマ

Skill がヒアリング結果を書き込み、`scripts/setup/*.sh` が読み込む **単一の真実の源**。

## スキーマ

```json
{
  "version": 1,
  "timestamp": "2026-05-27T10:00:00Z",
  "roles": ["PM", "Engineer"],
  "processes": ["requirement", "implementation", "review"],
  "notify": "slack",
  "mcp": {
    "predefined": ["playwright", "context7"],
    "custom": [
      {
        "name": "internal-x",
        "type": "stdio",
        "command": "node",
        "args": ["/path/to/server.js"],
        "env": {}
      }
    ]
  },
  "q4": "既存コードのスキャン",
  "q4_additions": {
    "agents": [],
    "commands": ["scan-codebase"],
    "skills": ["scan-codebase"]
  },
  "q4_handled": false
}
```

## フィールド

| フィールド | 型 | 必須 | 説明 |
|-----------|---|-----|------|
| `version` | number | ✓ | スキーマバージョン。現在は `1` |
| `timestamp` | string (ISO 8601) | ✓ | 作成 / 最終更新時刻 |
| `roles` | string[] | ✓ | Q1 の選択結果。`references/hearing.md` の Q1 キー一覧から |
| `processes` | string[] | ✓ | Q2 の選択結果 |
| `notify` | string | ✓ | Q3-1 の選択結果。`none` / `slack` / `discord` / `telegram` |
| `mcp.predefined` | string[] | ✓ | Q3-2 で既知 MCP から選んだもの |
| `mcp.custom` | object[] | ✓ | Q3-2 の自由記述分。完成形 `{ name, type, command, args, env }` |
| `q4` | string | ✓ | Q4 の自由記述回答。空文字許容 |
| `q4_additions.agents` | string[] | ✓ | Step 5-2 の Q4 事前解決で find-skill が特定した Agent 名（basename） |
| `q4_additions.commands` | string[] | ✓ | 同 Command 名（`/tkm:` プレフィックス無しの basename） |
| `q4_additions.skills` | string[] | ✓ | 同 Skill 名 |
| `q4_handled` | boolean | ✓ | Step 6 の Q4 残作業が完了したかどうか |

`q4_additions` は **Step 5-2（prune の前）** で書き込まれる。これにより prune.sh が Q4 で必要な Agent / Command を誤って削除しないようにする。

## ライフサイクル

1. Skill が Q1 開始時に空の state を作成（`q4_handled: false`）
2. 各質問の回答後、Skill が該当フィールドを更新
3. Step 5 で scripts が読む（書かない）
4. Step 6 完了後、Skill が `q4_handled: true` に更新
5. Skill が完了サマリを出した後もファイルは残置（再実行検知用）

## 再実行時の扱い

`/setup-project` 再実行時、Skill は `.setup-state.json` の有無で挙動を分岐：

- 存在しない → 通常の Q1〜Q4 フロー
- 存在する → ユーザーに「前回の続きから / やり直し / 中止」を会話で確認
