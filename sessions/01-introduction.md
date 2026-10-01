# Session 01: Lifecycle And System Thinking

**Incident.** A data scientist hands over `baseline.py`. It reads two CSV files, trains a
model, prints a ROC AUC of 0.76, and saves a pickle. The business wants predictions in the
checkout flow next quarter. Everyone in the room agrees the model is fine. Nobody can say
what happens next.

**Goal.** See the whole lifecycle before touching any tool, and leave with a list of
everything that has to be true for a prediction to be trusted a year from now.

## The Problem

A T-shirt shop sells online. Some customers come back and spend far more than the rest. If
the shop could tell, at a customer's first order, who will become high-revenue, it could
spend its retention budget on them. The target is binary: total spend above 300 is
`high_revenue`.

## The Data

Two files in `data/01_raw/`, committed to Git for now.

`customers.csv`, one row per customer:

| Column | Meaning |
|---|---|
| `customerID` | identifier, joins to `orders.customer_id` |
| `gender` | M or F |
| `birthdate` | `YYYY/M/D`; three rows fall on February 29 of a non-leap year |
| `user_agent` | browser string at sign-up; the script parses browser and OS from it |
| `ip_address` | dropped before modeling |
| `campaign` | whether the customer arrived through a campaign |
| `ip_address_country` | country resolved from the IP |

`orders.csv`, one row per order line:

| Column | Meaning |
|---|---|
| `order_date` | `YYYY/MM/DD` |
| `pages_visited` | pages viewed in the session that produced the order |
| `order_id` | identifier |
| `customer_id` | joins to `customers.customerID` |
| `tshirt_category` | four categories, written two different ways in the raw data |
| `tshirt_price`, `tshirt_quantity` | multiplied to get the line total |

Features used by the baseline: `pages_visited`, `age_first_order`, `gender`, `campaign`,
`ip_address_country`, `browser`, `os`.

## The Lifecycle

CRISP-DM (ASI module 2) describes the loop: business understanding, data understanding,
preparation, modeling, evaluation, deployment. `baseline.py` covers the middle four steps
in 150 lines. The course is about the loop closing: deployment produces new data, new data
changes the model's world, and the model has to be retrained, re-evaluated, and redeployed
without anyone redoing the first five steps by hand.

The question every student should be able to answer by session 12:

> What code, environment, data, parameters, model, image, deployment, and monitoring
> evidence produced the prediction I am looking at right now, and what happens when it
> stops working?

Each noun in that sentence is a session.

## In Class

1. Run `baseline.py`. Note the Python version, the package versions, and the three metrics.
2. Read the script top to bottom. Every `COURSE NOTE` comment marks a production risk. For
   each one, write down in one sentence what goes wrong if it is left as is.
3. In pairs, list what has to be true for a prediction from this model to be trusted in the
   checkout flow in twelve months. Group the list under the nouns in the question above.
4. Compare the group's list with the syllabus in the README. Anything on the list that no
   session covers is worth raising now.

## Reading

- ASI module 1 deck (introduction) and module 2 deck (ML model lifecycle), with the CRISP-DM
  notes.
- ASI module 9, decks 1 and 6: IT system architecture and sourcing strategy. Skim them; they
  frame the build-or-buy choices the course makes in sessions 5, 6, and 12.

## Homework

Run `baseline.py` on a second machine, or in a fresh virtual environment, or ask a classmate
to run it from a clean clone. Record whether it ran, which versions were installed, and
whether the three metrics match. Bring the record to session 2, where the differences are
the lab.

Start looking for a dataset. The graded project is built on the student's own problem and
data, not on HighRev; [PROJECT.md](../PROJECT.md) has the rules a dataset has to meet and
the proposal template. The proposal is due by the session 3 deadline, so two weeks of
looking start now.

## Checklist

- [ ] `baseline.py` runs locally and the metrics are recorded with the versions that produced them
- [ ] Each `COURSE NOTE` has a one-sentence failure written next to it
- [ ] The pair's trust list is grouped under the nouns of the course question
- [ ] The homework record exists, even if the second run failed; a failure is a result
