# Keeping this repository useful

Describe each change in terms of the problem, the change made, and the result
you actually observed. Keep proposed work separate from verified deployment.

Before committing live files, replace passwords, tokens, API keys, VPN keys,
private endpoints, and personal identifiers with placeholders. Git ignore rules
reduce accidental additions but do not inspect content or remove tracked data.
Never add application databases, backup archives, or full diagnostic exports.

For Compose imports, work on a copy. Replace literal secrets as well as values
loaded from environment files. Even uninterpolated Compose output can contain
literal credentials. Keep the original live files private.

Record test commands and results with code changes. For operational changes,
document prerequisites, the backup or rollback procedure, and a verification
step. Record failures and limitations as well as successes.
