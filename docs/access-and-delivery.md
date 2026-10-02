# Access and portable delivery

## Current MSI review — September 30, 2026

Fetched current remote branch and verified draft PR #1 at `d70f6666c4a0d38994eea2d33e1359529b972b2c`, base/main `6d78c043caba808e78c5790a24f171432fa2745c`. The prior MSI branch at `916a1d608fd87d28b33f0ee311806e410edec1d3` diverges and was preserved unchanged. A separate detached review worktree starts from the exact remote head. No branch/repository/PR was recreated. Recheck remote before publishing, integrate any new Pi commits, and update only the existing branch without force. Keep PR draft and unmerged. Historical access/portable-delivery instructions below are not instructions to create another branch or PR.

## Historical Pi continuation before publication — September 29, 2026

Existing draft PR #1 was read and attached to this chat. Its head is
8d11e96b4b9d9b84cec2dd90290451cae0c9cc51. No usable local homelab checkout was
found in the bounded search. Files, blobs, trees and both existing Git commits
were retrieved through the authorized GitHub connector; exact object IDs were
verified while reconstructing the local checkout. Work uses separate local
branch codex/pi-baseline-2026-09-29, preserving the existing history.
No earlier user working tree was overwritten. Remote branch/PR updates remain
pending under the current request's remote-change approval requirement.
No Drive/Gmail/Calendar data or synchronization was used in this continuation.

## Earlier access — September 29, 2026

Authenticated creation of `codex/homelab-operations-2026-09-23` from main
`6d78c043caba808e78c5790a24f171432fa2745c` succeeded. Before creation, a full
branch listing found only main and the all-state PR search returned none.
This actual write supersedes the earlier permission failure below. Continue
delivery through the implementation branch and a draft PR; do not merge or
change the Pi automatically. Check the repository's current PR list before
creating another review.

## Historical access checks

Rechecked on 2026-09-27, continuing the existing local branch:

- Repository metadata, branch listing and the all-state issues collection were
  readable. Remote `main` remains at
  `6d78c043caba808e78c5790a24f171432fa2745c`; it is the only remote branch.
- The repository metadata reports account-level admin/push permissions.
- The active GitHub connection returned `installations: []`.
- Creating `codex/homelab-operations-2026-09-23` from the existing main commit
  returned HTTP 403: `Resource not accessible by integration`.
- Creating the inventory issue returned the same 403. A search before the
  attempt found no existing issues or PRs. No issue was created.
- GitHub CLI was not found on the local PATH. Git Credential Manager's browser
  login options were verified through its local help. A credential-list check
  within the sandbox could not access the Windows credential store; that check
  does not establish whether a saved account exists outside the sandbox.
- A noninteractive HTTPS push outside the sandbox reached normal authentication
  and failed with `Cannot prompt because user interactivity has been disabled`
  and:
  `could not read Username for 'https://github.com': terminal prompts disabled`.
  No usable authenticated local login was available to finish the push. No remote
  implementation branch, issue, or PR was created, and nothing was merged.

The initial 2026-09-23 delivery had the same integration 403 and unavailable
local authentication. The renewed checks above supersede that access snapshot;
the original implementation and local branch were preserved.

The account permissions field does not prove the active integration has write
access. The precise observed blocker is rejection of branch and issue writes;
the underlying installation/permission mismatch cannot be identified more
narrowly from the available metadata. Do not repeatedly retry unchanged writes
or bypass the integration with extracted credentials.

## Supported access repair

In GitHub, open **Settings > Applications > Installed GitHub Apps** and find
the app used by the active GitHub connection. Choose **Configure**, then under
repository access select `finntucky1/homelab` and save. If that app is absent,
use the connection's normal install/reconnect flow for the `finntucky1` account.
Review the app's requested permissions; selecting a repository does not grant
permissions the app never requested. The requested tasks need Contents write,
Issues write, and Pull requests write. No workflow files are added here.

GitHub describes [installation/repository access settings](https://docs.github.com/en/apps/using-github-apps/reviewing-and-modifying-installed-github-apps)
and the write permissions for [branches](https://docs.github.com/en/rest/git/refs#create-a-reference),
[issues](https://docs.github.com/en/rest/issues/issues#create-an-issue), and
[pull requests](https://docs.github.com/en/rest/pulls/pulls#create-a-pull-request).
If the connector does not request the needed permissions, use a supported Git
client login instead; account admin status does not repair that connector.

For an existing Git Credential Manager installation, the locally verified
browser-login command is:

```sh
git credential-manager github login --username finntucky1 --browser
```

Complete the login in the browser yourself. If using an already-installed
GitHub CLI, `gh auth login --hostname github.com --git-protocol https --web`
is its [supported browser flow](https://cli.github.com/manual/gh_auth_login).
Use a working secure credential store; do not opt into insecure storage or
paste tokens, passwords, or recovery codes into this conversation.

## Portable change set

Delivery supplies a Git format patch based on
`6d78c043caba808e78c5790a24f171432fa2745c`, a source ZIP, issue drafts, PR text,
and application instructions. Keep an existing working tree intact; apply the
patch in a clean checkout on a separate branch, run the documented tests, and
inspect the staged changes before pushing. If the base has changed, review the
differences; do not force apply, reset, or overwrite local work.

The draft PR was subsequently created. Continue **existing PR #1**; do not
repeat the historical create commands below. Create issues only when needed and absent. Do not merge the PR as part
of this delivery. No live Pi action follows automatically from publishing code.
For an authenticated GitHub CLI, use `gh pr create --draft` with the prepared
title/body and explicit `--base main` and `--head codex/homelab-operations-2026-09-23`.
The [GitHub CLI reference](https://cli.github.com/manual/gh_pr_create) documents
the draft option. Recheck existing PRs before creation, just as for issues.
