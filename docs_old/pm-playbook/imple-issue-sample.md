## Overview

担当者イベント一覧画面（Epic #xxx）において、以下の機能を実装する：

1. **掲載されたアイテムIDをレスポンスに含める**（元々のスコープ）
2. **アイテムの詳細情報を追加**（#xxx コメント要件）
   - 掲載者名 (organizerName) - **EVENT.ORGANIZER_NAME から取得**
   - 掲載日時 (postedDatetime) - **既存で対応済み**
   - アイテムごとの目安時間 (estimatedTime)
   - オフライン対応フラグ (containsSpecialContent, containsStreamingContent)
3. **Program/Item API の並列呼び出し**（パフォーマンス改善）

**親Issue:** #xxx (担当者イベント一覧)
**依存Issue:** #xxx（テーブル定義・掲載API）

---

## 実装計画

### 修正方針

- **方針A採用**: 既存の `ProgramRepository`, `ItemRepository`, `ProgramEnrichmentInfo` 構造を活かして並列化を追加
- PR #xxx の goroutine 設定・並列処理パターンを参考に実装

---

## 1. event-manager-posting (Backend)

### A. Organizer情報の追加

| # | ファイル | 修正内容 |
|---|---------|---------|
| 1 | `domain/event/exist_event.go` | Organizer フィールド追加 |
| 2 | `repository/db/event/event_repository.go` | `FindBy(participantID, organizationCode)` で Organizer 情報を ExistEvent に設定 |
| 3 | `controller/event/dto/get_event_response.go` | `NewEventResponse(ExistEvent)` で `Organizer: nil` → `NewOrganizerResponse()` に修正 |

**実装詳細:**

```go
// exist_event.go - Organizer フィールド追加
type ExistEvent struct {
	ID         EventID
	Name       EventName
	PostedAt   time.Time
	DeadlineAt time.Time
	Programs   []Program
	PostStatus PostStatus
	Organizer  *Organizer // ★追加
}

func NewExistEvent(
	id EventID,
	name EventName,
	postedAt time.Time,
	deadlineAt time.Time,
	programs []Program,
	postStatus PostStatus,
	organizer *Organizer, // ★追加
) *ExistEvent {
	return &ExistEvent{
		ID:         id,
		Name:       name,
		PostedAt:   postedAt,
		DeadlineAt: deadlineAt,
		Programs:   programs,
		PostStatus: postStatus,
		Organizer:  organizer,
	}
}
```

```go
// get_event_response.go - organizer 返却
func NewEventResponse(event *ExistEvent, enrichmentMap map[string]ProgramEnrichmentInfo) *EventResponse {
	var organizerResp *OrganizerResponse
	if event.Organizer != nil {
		organizerResp = NewOrganizerResponse(event.Organizer) // ★修正
	}
	return &EventResponse{
		ID:         event.ID.Value(),
		Name:       event.Name.Value(),
		PostedAt:   event.PostedAt,
		DeadlineAt: event.DeadlineAt,
		Organizer:  organizerResp,
		// ...
	}
}
```

### B. 並列処理の実装

| # | ファイル | 修正内容 |
|---|---------|---------|
| 4 | `config/async.go` | **新規作成** - タイムアウト設定の定義 |
| 5 | `config/config.yaml` | `app.async` 設定追加 |
| 6 | `service/event/event_service.go` | `getProgramEnrichmentInfo()` を goroutine で並列化 |
| 7 | `service/event/event_service.go` | `getProgramEnrichmentInfoForParticipant()` を goroutine で並列化 |

**実装詳細:**

```yaml
# config.yaml
app:
  async:
    timeout-seconds: ${APP_ASYNC_TIMEOUT_SECONDS:5}
```

```go
// config/async.go - 新規作成
package config

import "time"

type AsyncConfig struct {
	TimeoutSeconds int `yaml:"timeout-seconds"`
}

func (c *AsyncConfig) Timeout() time.Duration {
	return time.Duration(c.TimeoutSeconds) * time.Second
}
```

```go
// event_service.go - 並列処理
func (s *EventService) getProgramEnrichmentInfoForParticipant(
	ctx context.Context,
	events []*ExistEvent,
) (map[string]map[string]ProgramEnrichmentInfo, error) {
	if len(events) == 0 {
		return map[string]map[string]ProgramEnrichmentInfo{}, nil
	}

	ctx, cancel := context.WithTimeout(ctx, s.config.Async.Timeout())
	defer cancel()

	programsForPackAPI := collectProgramsForPackAPI(events)
	programsForItemAPI := collectProgramsForItemAPI(events)

	// ★ goroutine で並列API呼び出し
	type packResult struct {
		data map[string]ProgramInfo
		err  error
	}
	type itemResult struct {
		data map[string][]ItemSummary
		err  error
	}

	packCh := make(chan packResult, 1)
	itemCh := make(chan itemResult, 1)

	go func() {
		data, err := s.getPackResults(ctx, programsForPackAPI)
		packCh <- packResult{data, err}
	}()

	go func() {
		data, err := s.getItemResults(ctx, programsForItemAPI)
		itemCh <- itemResult{data, err}
	}()

	// ★ 両方の結果を待機
	packRes := <-packCh
	if packRes.err != nil {
		return nil, packRes.err
	}
	itemRes := <-itemCh
	if itemRes.err != nil {
		return nil, itemRes.err
	}

	// Build result map
	// ...
}
```

---

## 修正ファイル数まとめ

| リポジトリ | 新規 | 修正 | 計 |
|-----------|-----|-----|-----|
| event-manager-posting | 1 | 3 | **4** |
| **合計** | **1** | **3** | **4** |

---

## Request/Response

### 担当者イベント一覧取得API (GET /events)

**リクエスト:**
```
GET /events?participantId=xxx&organizationCode=xxx
```

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|-----|------|
| participantId | String | ○ | 参加者ID |
| organizationCode | String | ○ | 組織コード |

**レスポンス:**
```json
{
  "events": [
    {
      "id": "event-001",
      "name": "イベント名",
      "organizer": {
        "id": "organizer-001",
        "name": "山田太郎"
      },
      "postedDatetime": "2025-01-15T09:00:00",
      "deadlineDatetime": "2025-01-22T23:59:59",
      "programs": [
        {
          "id": "program-001",
          "code": "1-1",
          "name": "プログラム名",
          "ageGroup": "A30",
          "category": "WORKSHOP",
          "contentType": "STANDARD",
          "itemIds": ["i-001", "i-002"],
          "items": [
            {
              "itemId": "i-001",
              "estimatedTime": 60,
              "containsSpecialContent": false,
              "containsStreamingContent": false
            }
          ],
          "totalItem": 2,
          "totalEstimatedTime": 150,
          "containsSpecialContent": true,
          "containsStreamingContent": false
        }
      ]
    }
  ]
}
```

---

## UT

### event-manager-posting

- `ExistEvent` に Organizer 情報が設定されること
- `NewEventResponse(ExistEvent)` で organizer が返却されること
- Pack API と Item API が並列で呼び出されること
- タイムアウト時に適切なエラーが返却されること

---

## Acceptance Criteria

- [x] 担当者イベント一覧APIで `itemIds` が返却される（既存で対応済み）
- [x] アイテム詳細情報 (`items`, `totalItem`, `totalEstimatedTime`, etc.) が返却される（既存で対応済み）
- [ ] `organizer.name` が返却される（EVENT.ORGANIZER_NAME から取得）
- [ ] Pack API と Item API が並列で呼び出される

---

## 備考

### 並列処理の設定値

| 項目 | デフォルト値 | 環境変数 |
|------|------------|---------|
| タイムアウト（秒） | 5 | `APP_ASYNC_TIMEOUT_SECONDS` |

### 依存関係

```
#xxx (POST /items/summary) ← 完了済み
#xxx (Pack POST /programs/info) ← 完了済み
```