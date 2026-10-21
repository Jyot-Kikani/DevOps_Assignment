# P18: one update and Git rollback

1. Save the current deploy revision/release and a browser screenshot.
2. Make a small visible UI change on a `codex/` branch. Open a PR and wait for
   both current-head required CI jobs. Merge only with an up-to-date branch.
3. Successful main CI triggers the release workflow: build, scan, publish and
   generated deploy commit. Run `gitops-check`, public smoke and inspect the
   visible change/source metadata. Record the PR, run and deploy revision.
4. In a separate checkout of **deploy**, use `git revert <update-deploy-commit>`
   and push normally. Do not force-push or use `kubectl rollout undo` while
   self-heal is enabled. Run `gitops-check` and public smoke; verify the prior
   visible version, source and digests are restored.

Revert only application manifests/metadata. The v1 database remains in place;
do not restore a dump or downgrade a schema as an application rollback. A later
main CI release will promote current main again; the demonstrated rollback is
the latest commit on deploy until another deliberate publication.

Batch 5 records actual before/update/rollback evidence. P19 is a separate phase.
