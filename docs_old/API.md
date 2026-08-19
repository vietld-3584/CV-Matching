# API ドキュメント

プロジェクトで提供する API の仕様を OpenAPI 3.1.0 形式で記載する。

## 概要

<!-- API の目的・スコープ・対象範囲を記載 -->

## OpenAPI 仕様

```yaml
openapi: 3.1.0
info:
  title: <API 名>
  version: 0.1.0
  description: |
    <API の概要を記載>
servers:
  - url: https://api.example.com
    description: 本番環境
  - url: https://staging.api.example.com
    description: ステージング環境

tags:
  - name: example
    description: サンプルリソース

paths:
  /examples:
    get:
      tags: [example]
      summary: サンプル一覧取得
      operationId: listExamples
      parameters:
        - in: query
          name: limit
          schema:
            type: integer
            default: 20
      responses:
        "200":
          description: OK
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: "#/components/schemas/Example"
        "401":
          $ref: "#/components/responses/Unauthorized"

components:
  schemas:
    Example:
      type: object
      required: [id, name]
      properties:
        id:
          type: string
          format: uuid
        name:
          type: string
        createdAt:
          type: string
          format: date-time

    Error:
      type: object
      required: [code, message]
      properties:
        code:
          type: string
        message:
          type: string
        details:
          type: object
          additionalProperties: true

  responses:
    Unauthorized:
      description: 認証エラー
      content:
        application/json:
          schema:
            $ref: "#/components/schemas/Error"

  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

security:
  - bearerAuth: []
```

## 補足

- 上記はあくまで雛形なので、プロジェクトに合わせて `info`, `servers`, `paths`, `components` を埋めること
- 仕様の単一ソースとしたい場合は、本ファイルから OpenAPI 部分を `docs/openapi.yaml` 等に切り出して lint / codegen に利用しても良い
