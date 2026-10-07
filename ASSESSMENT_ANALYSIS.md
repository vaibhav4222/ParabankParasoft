# Assessment analysis

Source: `D:\DOWNLOADS_FILES\QA_Automation_Assignment.pdf`.

The document assesses senior-level framework design and handling of transactional
state, rather than just successful UI clicks. It permits Playwright TypeScript or
Python, expects roughly two days of effort, and targets ParaBank.

| Phase | Acceptance criteria | Project implementation |
| --- | --- | --- |
| Architecture | Modular framework, custom HTML report, glassmorphism cards, exact orange accent | Page objects, API client, reusable data/currency/lock modules, bespoke pytest report |
| A | API reset and Web Service provider before UI; unique registration; new Checking; approved loan; extracted loan ID and deposited balance | Session sandbox fixture, module loan-user fixture, UI balance assertion |
| B | Same user; three different UI transfers; Find Transactions HTML table; parse USD; sum and reconcile source deductions | Three amounts totaling $184.49; per-transfer multiset and both accounts' balance deltas |
| C | Browserless API user, funds deposit, transaction history, exact declared contract | HTTP registration plus REST JSON; TypeScript interface and strict JSON Schema |
| Decisions | Explain shared-state contention, floating point, API/UI separation | `DECISIONS.md` |
| Submission | Public GitHub/GitLab URL; dependency, headless-run and report commands | GitHub repository at https://github.com/vaibhav4222/ParabankParasoft and README |

## Important traps

1. A unique username cannot protect against another worker's global database reset.
   Coordinated workers must hold a shared lock for the entire suite; uncontrolled
   public users require a private instance for actual isolation.
2. Dynamic account dropdowns must be awaited by their rendered data, never sleeps.
3. Currency aggregation must use integer cents, including comma-formatted amounts.
4. TypeScript types do not validate a live HTTP response. Runtime schema enforcement
   must reject missing properties, extra properties and incorrect field types.
5. A and B share one user by design. Fixture-driven setup supports B when selected
   on its own and avoids implicit reliance on test execution order.
6. Live ParaBank JSON emits epoch-millisecond dates, and its credentials have a
   practical 20-character limit. The generated 19-character values fit those fields.
7. Test artifact screenshots and traces can expose request data. Keep artifacts
   out of a public submission repository.

## Scope of creation

The PDF is a specification for the local project requested by the user. Its
submission instructions do not themselves authorize publication to an external
account. The user subsequently authorized publishing this project to
`https://github.com/vaibhav4222/ParabankParasoft`.
