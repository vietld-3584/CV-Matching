---
name: Feature Frontend Development
about: Template for new frontend feature development
title: '[Feature-Frontend] '
labels: ['feature', 'frontend']
assignees: ''
---

## Overview
<!-- Brief description of the feature -->


## Implementation


### 新規作成

- xx/xxx.tsx

### 更新対象

- xx/xxx.tsx

## 型定義とインターフェース

### フォームスキーマ（Zod）

```typescript
const SampleSchema = z.object({
  keyword: z.string().optional().nullable(),
});
```

### コンポーネントProps
```typescript
// Button
type Props = React.ComponentProps<'button'>

```

### カスタムフック型定義
```typescript
type UseCustomHooksOptions = {
    hoge: string;
};

type UseCustomHooksReturn = {
    huga: string;
};

type UseCustomHooks = (options: UseCustomHooksOptions) => UseCustomHooksReturn
```

### 定数
```typescript
export const SAMPLE_TYPES = {
    typeA: 'a',
    typeB: 'b',
} as const;
```

## Figmaリンク

## 備考

