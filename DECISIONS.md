# Architectural Decision Record

## 1. State contention and global resets

**Decision:** UUID-generated 64-bit random username suffixes make user identity
collisions extremely unlikely while fitting ParaBank's 20-character columns. Global
state is separately controlled: reset only once per session, execute scenarios
serially, and hold a Redis lock throughout setup, tests and teardown in CI.
The lock key includes the canonical base URL, so unrelated private deployments
can run independently. All clients must use the same Redis and URL spelling.
If the lock cannot be acquired, reset is refused. A renewable 120-second lease
avoids an indefinite stale lock after a crashed worker. Ownership is checked
before reset, each scenario, and each transactional mutation.

**Limit:** This prevents collisions between cooperating workers. Neither UUIDs,
CI concurrency groups nor Redis can prevent an unrelated engineer from resetting
the public ParaBank database. Claiming absolute protection on a public sandbox
would be incorrect. Use one private ParaBank instance per CI worker for reliable
isolation, or reserve an instance and require every writer to honor the lock.
An expired lease cannot fence a request already in flight because ParaBank has
no server-side fencing token support. Loss of ownership aborts subsequent work;
it is not retried blindly. The Redis outage/renewal path should be validated
against your deployment before production CI use.

Global admin settings are deliberately normalized to $1,000 initial balance,
$100 minimum balance, Web Service provider, down-payment processor and 10%
threshold. This produces deterministic loan approval and affordable transfers.
Settings are read back after saving. No cleanup reset occurs at teardown, which
would create another destructive window. Explicit reset authorization is
required by the command-line guard. Unconfigured CI and pytest-xdist workers fail
early. Default local tests do not touch the sandbox.

## 2. Currency precision

**Decision:** Treat USD as integer cents for every sum and comparison. Parse strings
using `Decimal`, remove only validated currency formatting and multiply by 100.
The parser accepts grouped thousands and up to two decimal places and rejects
malformed grouping, excess fractional precision, exponent notation and NaN.
REST JSON decimals are also decoded directly to `Decimal`, never through a float.

Thus $150 + $25.50 + $8.99 becomes `15000 + 2550 + 899 = 18449` cents.
No epsilon or rounded floating-point comparison can conceal a one-cent defect.
For a TypeScript implementation the same decision would use validated string-to-
integer parsing (or a decimal library), not JavaScript `parseFloat` arithmetic.
The permitted Python stack gives exact decimal parsing without another dependency.

Scenario B compares the multiset of extracted debit values to the three requested
amounts, their sum to the source account's balance reduction, and the destination's
increase. Filtering by the exact outgoing transfer description excludes the loan
credit and unrelated transaction types. Table columns are mapped by their headers
rather than assuming a fixed currency-column position.

## 3. Design pattern and API/UI boundary

**Decision:** Strict Page Object Model. UI page objects own selectors, interactions,
retrying DOM assertions and table extraction. Tests own business expectations.
API clients own administrative HTTP calls, API registration and REST resource
access. Fixtures own lifecycle, locking and explicit cross-scenario state.

Scenario A performs reset/settings through HTTP before opening its browser,
then registers, opens Checking and requests the loan through the UI. Scenario B
keeps that same authenticated customer and exercises transfers and Find Transactions
through the UI. API shortcuts do not replace the required user workflows.
Scenario C uses only `APIRequestContext`, with no page/browser fixture. ParaBank's
REST contract does not expose a register-customer endpoint, so registration uses
the application HTTP form; funds and transaction verification use REST endpoints.

Dropdown waits assert that the dynamically discovered account option exists and
has numeric text before selecting it. Account and balance waits assert rendered
values. There are no fixed browser sleeps or wait-for-timeout calls.

The TypeScript interface documents the requested contract even though execution
uses Python. JSON Schema enforces exact required properties and rejects unknown
keys; this is necessary because TypeScript interfaces alone are erased at runtime.
Schema tests intentionally cover extra keys, missing fields, wrong types, enum
drift and malformed dates. Live JSON exposes dates as epoch milliseconds (the WADL
describes the XML representation as dateTime), so the exact JSON contract requires
a nonnegative integer, not an ISO string. The interface and schema must be reviewed together
when the service contract changes.

## 4. Custom reporting and failure evidence

**Decision:** Generate a standalone HTML dashboard and JSON from pytest lifecycle
hooks, including setup and teardown failures. The glass cards use alpha backgrounds,
backdrop blur, borders and layered shadows. The exact accent `#F48031` is used for
headers, active filters and passing indicators. Status text keeps meaning visible
without depending only on color. Responsive cards and keyboard-focus styling
support narrow screens and keyboard navigation.

All test names and failure text are HTML-escaped. Filtering runs locally with no
CDN or third-party scripts. Tests are reported once with aggregate phase duration;
a teardown failure overrides a passing call. Screenshots and a workflow trace
support diagnosis. Artifacts are ignored by Git because traces can include test
passwords and request data.
