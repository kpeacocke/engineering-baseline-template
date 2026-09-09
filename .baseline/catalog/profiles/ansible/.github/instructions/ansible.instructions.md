---
applyTo: "**/*.yml,**/*.yaml,galaxy.yml,meta/**,roles/**,plugins/**,playbooks/**"
---

# Ansible instructions

- Prefer Ansible modules over `ansible.builtin.shell` or `ansible.builtin.command`; use shell/command only when no suitable module exists and make idempotence/error handling explicit.
- Use FQCNs in shared automation content.
- Prefer certified/supported collections for enterprise AAP use when they satisfy the requirement; document community-only dependencies and support implications.
- Design tasks for idempotence and meaningful check-mode behaviour where the underlying operation supports it.
- Keep secrets in credential/vault mechanisms, never vars files or logs; use `no_log` narrowly around sensitive values rather than hiding whole workflows.
- Make `changed_when` and `failed_when` reflect the real operation when commands or unusual modules require them.
- Use handlers for state transitions that should occur only after a change.
- Pin collection dependencies deliberately and review upgrades for behavioural/support impact.
- Validate content with ansible-lint and syntax checks; use Molecule/integration tests where behaviour warrants it.
- Consider Execution Environment dependencies and AAP/controller/EDA compatibility, not only local ansible-core behaviour.
