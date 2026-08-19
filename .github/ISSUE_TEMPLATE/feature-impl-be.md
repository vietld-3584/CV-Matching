---
name: Feature Development
about: Template for new feature development
title: '[Feature-Backend] '
labels: ['feature', 'backend']
assignees: ''
---

## Overview
<!-- Brief description of the feature -->


## Implementation


### 新規作成

- xxx/xxx/xxx.ts

### 更新対象

- xxx/xx.ts

## 型定義とインターフェース

### Migrations

**up**

```sql
```

**down**

```sql
```

### Domain

```typescript model/sample.ts
class Sample {
    private hoge: string;
    private fuga: number;

    constructor(hoge: string, fuga: number) {
        // 初期化処理
    }

    hogeFuga(param: string): boolean {
        // 実装
    }
}
```

```typescript repository/sample.ts
interface GetQuery {
    limit: number;
    offset: number;
    keyword: string;
}

interface CreateSample {
    hoge: string;
    fuga: number;
}

interface SampleRepository {
  get(query: GetQuery): Sample
  create(createSample: CreateSample): Sample
}
```

### Application

```typescript usecase/sample.ts
interface SampleUseCaseInput {
    hoge: string;
    fuga: number;
}

interface SampleUseCaseOutput {
    id: string;
    hoge: string;
    fuga: number;
    createdAt: Date;
}

class SampleUseCase {
    constructor(private sampleRepository: SampleRepository) {
        // 依存性注入
    }

    async execute(input: SampleUseCaseInput): Promise<SampleUseCaseOutput> {
        // ビジネスロジックの実装
    }

    async getList(query: GetQuery): Promise<SampleUseCaseOutput[]> {
        // 取得ロジックの実装
    }
}
```


### Interface

```typescript controller/sample.ts
interface CreateSampleRequest {
    hoge: string;
    fuga: number;
}

interface GetSampleListRequest {
    limit?: number;
    offset?: number;
    keyword?: string;
}

interface SampleResponse {
    id: string;
    hoge: string;
    fuga: number;
    createdAt: string;
}

class SampleController {
    constructor(private sampleUseCase: SampleUseCase) {
        // 依存性注入
    }

    async create(request: CreateSampleRequest): Promise<SampleResponse> {
        // リクエストのバリデーションと変換
    }

    async getList(request: GetSampleListRequest): Promise<SampleResponse[]> {
        // リクエストのバリデーションと変換
    }
}
```


### Infrastructure

```typescript repository/sample-repository-impl.ts
interface SampleEntity {
    id: string;
    hoge: string;
    fuga: number;
    created_at: Date;
    updated_at: Date;
}

class SampleRepositoryImpl implements SampleRepository {
    constructor(private db: DatabaseClient) {
        // データベース接続の注入
    }

    async get(query: GetQuery): Promise<Sample> {
        // データベースクエリの実行とドメインモデルへの変換
    }

    async create(createSample: CreateSample): Promise<Sample> {
        // データベースへの保存とドメインモデルへの変換
    }

    private toEntity(sample: Sample): SampleEntity {
        // ドメインモデルからエンティティへの変換
    }

    private toDomain(entity: SampleEntity): Sample {
        // エンティティからドメインモデルへの変換
    }
}
```

## テスト(optional)

### Unit Test

**Domain**

**Application**

**Interface**

**Infrastructure**

### エンドポイントテスト


## 備考

