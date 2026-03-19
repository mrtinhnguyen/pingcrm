# Changelog

All notable changes to PingCRM will be documented in this file.

## [Unreleased]

## [1.2.0] - 2026-03-19

### テーマ: AI バイオ抽出 & UX 改善

**連絡先のSNSバイオからAIで構造化データを自動抽出。アーカイブ操作の改善、同期の高速化、バグ修正も。**

---

#### 1. マジックワンド（AI バイオ抽出）

**今まで**: Twitter/Telegram/LinkedInのバイオに役職や会社名が書いてあっても、手動でコピペして連絡先に入力する必要があった。「Anders | LoopFi」のような名前も手動で分割が必要。

**今後**: 連絡先詳細パネルの杖アイコンをクリックすると、Claude Haiku がバイオを解析して構造化データを自動入力。

- 名前の正規化（「Anders | LoopFi」→ First: Anders, Company: LoopFi）
- 役職・会社名の抽出
- 会社のウェブサイト・業界・所在地を Organization レコードに反映
- ウェブサイトからロゴも自動ダウンロード

```
POST /api/v1/contacts/{id}/extract-bio
→ { "fields_updated": ["given_name", "company", "company_website"], "source": "ai_bio" }
```

#### 2. アーカイブ/アーカイブ解除トグル

**今まで**: アーカイブ済み連絡先を開いても、通常の連絡先と同じアーカイブボタンが表示。解除するにはプライオリティを手動で変更する必要があった。

**今後**: アーカイブ済み連絡先では ArchiveRestore アイコン（琥珀色ハイライト）を表示。クリックで即座にアーカイブ解除（priority → normal）。ページ遷移なし。

#### 3. LinkedIn 自動同期の高速化

**今まで**: LinkedIn メッセージの自動同期間隔が2時間。午前中にメッセージを送っても、UIに反映されるまで最大2時間待つ必要があった。サービスワーカーのログにもスキップ理由が表示されなかった。

**今後**: 同期間隔を15分に短縮。スロットル発動時にはサービスワーカーの DevTools コンソールに残り時間を表示。

```
[Sync] Skipped: throttle, last sync 8 min ago, next in 7 min
```

#### 4. アーカイブ済み連絡先の Twitter 同期除外

**今まで**: アーカイブした連絡先でも Twitter バイオのポーリングと DM 同期が継続。バイオ変更通知が届いてしまう。

**今後**: `poll_contacts_activity` と `_build_twitter_id_to_contact_map` の両方で `priority_level != 'archived'` フィルターを追加。

#### 5. バグ修正

- **Identity マージのクラッシュ修正**: ユニークフィールド（telegram_username等）の重複でマージが失敗する問題を解決 (#51)
- **Twitter DM 同期の 401 エラー処理**: トークンリフレッシュが正しく発火しなかった問題を修正
- **ドキュメントリンク修正**: セットアップガイドへの相対パスリンクを修正

#### 6. その他

- ブランド名を「PingCRM」に統一（全ファイル）
- Chrome 拡張機能を v1.5.5 にバンプ

---

## [1.1.0] - 2026-03-17

### テーマ: ダークモード対応

**全画面・全コンポーネントにダークモードを追加。目に優しいナイトモードで、夜間の利用が快適に。**

---

#### 1. テーマ切り替えトグル

**今まで**: ライトモード固定。夜間や暗い環境では画面が眩しく、目の疲れの原因に。

**今後**: ナビバーに Sun/Moon ピルトグルを設置。ワンクリックでライト/ダーク切り替え。

- OS のシステム設定（`prefers-color-scheme`）を自動検出
- 選択は `localStorage` に保存、次回訪問時も維持
- ページ読み込み時のフラッシュ（FOUC）防止スクリプト内蔵

#### 2. 全ページのダークモード対応

**今まで**: 白背景 + stone 系カラーのライトテーマのみ。

**今後**: Dashboard、Contacts、Settings、Suggestions、Notifications、Organizations、Identity、Auth、Onboarding — 全 20 ルートがダークモードに対応。

- ページ背景: `stone-50` → `stone-950`
- カード: `white` → `stone-900`
- ボーダー: `stone-200` → `stone-700`
- テキスト: コントラスト比 4.5:1 以上（WCAG AA 準拠）

#### 3. 全コンポーネントのダークモード対応

**今まで**: 共有コンポーネント（タイムライン、メッセージエディタ、CSV インポート等）はライトモード前提。

**今後**: 11 個の共有コンポーネントすべてに `dark:` バリアントを追加。

- Nav、EmptyState、ScoreBadge、ContactAvatar、Timeline
- MessageEditor、CsvImport、EditableField、InlineListField
- TagTaxonomyPanel、ActivityBreakdown、CompanyFavicon

#### 4. ブランドカラーの維持

**今まで**: Teal + Stone のブランドパレット。

**今後**: ダークモードでも Teal アクセントを維持。明るさを調整して暗い背景でも視認性を確保。

- アクティブリンク: `teal-700` → `teal-400`
- アクセント背景: `teal-50` → `teal-950`
- ステータスカラー（emerald/amber/red/sky）も同様に調整

---

## [1.0.0] - 2026-03-05

Initial release of PingCRM.
