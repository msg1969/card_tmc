# GitHub Actionsの更新と確認

毎週月曜09:30 JSTにDependabotがActionsの更新を確認する。保守者は更新PRと、
PRがない場合もInsights → Dependency graph → Dependabotの直近ジョブの成功を確認する。
失敗時は原因を調べて再実行する。重大な修正は次の週次チェックを待たない。

1. 公式リポジトリ由来のSHA、同じ行のバージョン注記、リリース内容を確認する。
   `upload-pages-artifact`内部の`upload-artifact`も確認し、必要なら許可リストを更新する。
2. 更新PRで公開前テスト・ビルド・Pages artifact作成の成功を確認する。
   PRではdeployを実行せず、`main`に入ってから既存のPages公開を行う。
3. マージ後はbuild・deployの成功と既存公開URLを確認する。公開ファイルの変更がある場合は
   READMEの表示・リンク・公開対象確認も行う。
4. 問題時は既知の安全なSHAへ戻すPRを作り、同じ検証を通す。
   SHA必須化を常時解除したり、可変タグへ戻したりして対処しない。

SHA必須化は既に有効。過去のタグ指定workflowの再実行はブロックされ得るため、
現在のmainからの実行を基本にする。Actions lockfile方式は今回は導入しない。

参考: [DependabotのSHAと注記更新](https://docs.github.com/en/code-security/reference/supply-chain-security/supported-ecosystems-and-repositories#github-actions)
