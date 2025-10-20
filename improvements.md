# コード構造の改善案

現在のコードベースをより堅牢で保守しやすくするための改善案です。

## 1. クラスと責務の分離

- **現状**: `main.py` に `RecipeManager`, `ResourceCalculator` という主要なクラスが含まれていますが、入力処理、製品の分類、メインループなどのロジックも同ファイルに混在しています。
- **提案**:
    - **`main.py`**: アプリケーションのエントリーポイントとメインループに特化させます。他の機能は別ファイルに切り出します。
    - **`calculator.py`**: `ResourceCalculator` クラスをこのファイルに移動します。計算ロジックの核心部分を独立させます。
    - **`recipe_manager.py`**: `RecipeManager` クラスをこのファイルに移動します。レシピの読み込みと管理の責務を明確に分離します。
    - **`input_parser.py`**: `process_input` や `fuzzy_match_item` などの入力解析ロジックをこのファイルにまとめます。
    - **`categorizer.py`**: `categorize_products` 関数をこのファイルに移動し、計算結果の分類ロジックを分離します。

これにより、各ファイルが単一の責務を持つようになり、コードの見通しが良くなります。

## 2. 循環参照の解消

- **現状**: `main.py` が `view.py` をインポートし、`view.py` も `main.py` から `Node` クラスをインポートしようとしています（コメントアウトされていますが、構造的な問題を示唆しています）。
- **提案**: `Node` クラスのような、複数のモジュールで共有されるデータ構造は、独立したファイル（例: `models.py` や `data_structures.py`）に定義します。これにより、モジュール間の循環依存を回避できます。

```python
# models.py
from typing import Dict, List, Optional, Tuple

class Node:
    def __init__(self, item: str, needed: float, depth: int):
        self.item = item
        self.needed = needed
        # ... 以下略
```

## 3. エラーハンドリングの強化

- **現状**: `_load_recipes_from_json` では `FileNotFoundError` と `json.JSONDecodeError` を処理していますが、他の部分では一般的な `Exception` で捕捉している箇所があります。
- **提案**: より具体的でカスタムな例外クラスを定義し、エラーの種類に応じたきめ細やかなハンドリングを行います。例えば、`ItemNotFoundError`, `InvalidRecipeError`, `CircularDependencyError` などを定義し、それぞれの状況で送出・捕捉するようにします。

```python
# exceptions.py
class CalculatorError(Exception):
    """Base exception for this application."""
    pass

class ItemNotFoundError(CalculatorError):
    """Raised when an item is not found in recipes."""
    pass

class InvalidInputError(CalculatorError):
    """Raised for malformed user input."""
    pass
```

## 4. テストの構造化とカバレッジ向上

- **現状**: `test.py` に全てのテストが記述されています。主要なシナリオはカバーされていますが、より複雑なケースやエッジケースのテストを追加する余地があります。
- **提案**:
    - **テストファイルの分割**: `tests/` ディレクトリを作成し、`test_calculator.py`, `test_recipe_manager.py` のように、テスト対象のモジュールごとにファイルを分割します。
    - **フィクスチャの利用**: `recipes.json` の内容に依存せず、テストごとに独立したレシピデータ（モックやテスト用の小さなJSON）を使用するようにします。これにより、テストの独立性が高まります。
    - **カバレッジの拡充**: 循環参照、在庫が完全に不足している場合、複数の代替レシピが存在する場合など、エッジケースのテストを追加します。

## 5. 型ヒントの徹底

- **現状**: 型ヒント（Type Hinting）が多くの箇所で利用されていますが、一部で `Optional` や `Union` の使用がさらに明確化できる箇所があります。
- **提案**: プロジェクト全体で型ヒントの記述を統一し、`mypy` などの静的解析ツールを導入して型安全性をさらに高めます。特に、辞書型（`Dict`）のキーと値の型をより厳密に定義することが有効です。

## 6. マジックナンバーの排除

- **現状**: `_find_best_route` 内のスコア計算で `1000` というマジックナンバーが使用されています。
- **提案**: このような数値は、意味を説明する名前を持つ定数として定義します。これにより、コードの意図が明確になり、将来の変更が容易になります。

```python
# calculator.py

# スコア計算における重み。基本資源のコストを工程数よりも優先する
BASE_RESOURCE_COST_WEIGHT = 1000

# ...

route_score = (sum(route_total_inputs_needed.values()) * BASE_RESOURCE_COST_WEIGHT) + num_sub_recipe_steps
```
