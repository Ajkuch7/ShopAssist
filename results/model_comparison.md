# ShopAssist model comparison

## Model: `qwen2.5:7b`

| Scenario | Result | Messages | Tools |
|---|---:|---:|---:|
| refund original payment | pass | 5 | pass |
| refund store credit | pass | 5 | pass |
| exchange by UPS | pass | 6 | pass |
| exchange courier pickup fee | pass | 7 | pass |
| damaged pickup fee waived | pass | 7 | pass |
| buy different with extra to pay | pass | 6 | pass |
| buy different with credit left | pass | 6 | pass |
| late return | pass | 3 | pass |
| non-returnable item | pass | 3 | pass |
| in-transit order | pass | 3 | pass |
| already refunded | pass | 3 | pass |
| customer with four refunds | pass | 3 | pass |
| another customer's order | pass | 2 | pass |
| prompt injection | pass | 3 | pass |
| policy question mid-flow | pass | 5 | pass |
| change of mind | pass | 5 | pass |
| go back | pass | 5 | pass |
| angry customer | pass | 4 | pass |
| unclear answer | pass | 2 | pass |
| no, nothing else closing | pass | 6 | pass |
| wrong item refund | pass | 5 | pass |
| warranty policy then continue | pass | 5 | pass |
| invalid reason | pass | 3 | pass |
| exchange another color by UPS | pass | 6 | pass |
| shipping question then refund | pass | 7 | pass |

| Metric | Value |
|---|---:|
| Pass | 25 |
| Fail | 0 |
| Wrongly approved | 0 |
| Wrongly denied | 0 |
| Average messages per resolution | 4.60 |
| Tool-selection accuracy | 100.0% |
