# Campus Customs Agent Desk: Design

The dashboard (`frontend/`, React + Vite + TypeScript) is a desk where a person sits with five AI coworkers. It keeps the Campus Customs identity from Homework 4 (Yale blue on white, calm and uncluttered) and pushes it toward **Bauhaus × Scandinavian minimalism**: geometry does the talking, color is rationed, and the page stays quiet until something needs you.

Run it with the backend on port 8000 (`cd backend && uvicorn main:app --reload --port 8000`) and `npm run dev` in `frontend/`. It talks to `http://localhost:8000`, and the backend allows `http://localhost:5173` through CORS.

## Layout: a three-column desk

```
┌──────────────────────────────────────────────────────────── 2px ink rule ─┐
│ ●■▲ Campus Customs                                          $3,400        │
├──────────────┬──────────────────────────────────┬─────────────────────────┤
│ TICKETS      │ RENT NOTICE · ELM CITY PROPERTIES │ NEEDS YOU (1)          │
│ 101 Bulldog  │ 102 Rent due        [Run the team]│ ▌$2,400  Pay rent      │
│ 102 Rent  ✓  │ ▌● The Boss's call                │ ▌[Approve]  Reject     │
│ 103 Hoodies  │ CONVERSATION                       │ THE TEAM               │
│              │ ● Boss   Read the ticket           │ ● Boss          DONE   │
│              │   │ ◗ Facilities  Read the lease   │ ■ Inventory  NOT NEEDED│
│              │   │ ▲ Accounting  Prepared payment │ ▲ Accounting    DONE   │
└──────────────┴──────────────────────────────────┴─────────────────────────┘
```

- **Left: Tickets.** The inbox. Each ticket is a big bold number (101, 102, 103) with its type, subject and requester. The selected ticket gets a thin Yale blue bar that slides in from the left edge.
- **Center: The floor.** The selected ticket's title, one primary button (**Run the team**), the Boss's final call, and the live conversation. This is the widest column because it's where the story happens.
- **Right: Needs you, then The team.** Human decisions sit at the top, because they're the only thing on the page that waits on a person. Below that, a roster of the five agents with their status and what each did.
- **Header: the money.** The checking balance is the single biggest element on the page, opposite the wordmark.

**Why:** The columns read left to right, just like the work flows: *what came in → what the team is doing → what I need to decide*. A 3 : 6 : 3 grid with 1px dividers instead of cards keeps it like a printed ledger rather than a pile of widgets. Generous padding and a single 2px rule under the masthead give the page a strong top edge, a Bauhaus poster move. Below 1080px the columns stack in the same order.

## Visual language

| Element | Choice | Why |
|---|---|---|
| Background | Off-white paper `#f6f4ef`; white only for the selected ticket and the decision card | Warmer and calmer than pure white for a screen you sit at all day. White becomes a highlight. |
| Primary color | Yale blue `#00356b` | Campus Customs identity: headings, ticket numbers, the run button, the "resolved" mark. |
| Accent | Mustard `#e1a72b`, used **only** for "needs a human" | The approval card, the Approve button and the count badge. If you see yellow, it's your turn. |
| Type | **Jost** (a free geometric sans in the Futura family), bold 700 headings with tight tracking, small-caps labels with wide tracking | Futura is the Bauhaus typeface. Big bold numbers and quiet uppercase labels create a clear hierarchy without boxes. |
| Lines | 1px warm-gray rules, one 2px ink rule | Structure from lines, not shadows. |
| Surfaces | Flat fills, square corners on buttons, no shadows, no gradients | Scandinavian restraint, and nothing competes with the content. |

## How agents look different: a shape for each voice

Every agent has a **flat geometric shape and its own color**, drawn as an inline SVG and used everywhere that agent appears (the feed, the team roster, handoff arrows and chips). You can tell who's talking from across the room, even without reading the name.

| Agent | Shape | Color | Why this shape |
|---|---|---|---|
| Boss | ● circle | Yale blue | The center everyone reports to; also the brand color. |
| Inventory | ■ square | Light blue | Boxes on shelves. |
| Accounting | ▲ triangle | Ink black | Sharp and exact: the ledger, the bottom line. |
| Facilities | ◗ half circle | Bauhaus red | An arch or doorway: the building itself. |
| Customer Service | ▢ rounded square | Sage green | The friendliest shape for the agent who speaks to people. |

The palette is the Bauhaus primary trio of blue, red and black, plus a calm green. Yellow is held back for the human, so the agents never borrow the "attention" color.

Other details that tell agents apart:
- **Names are written in the agent's color** in the feed, so a run of Facilities lines turns red down the page.
- **Delegation depth is indented with a thin rail.** When the Boss asks Facilities, Facilities' steps shift right along a 1px line, so you can see who is working for whom.
- **Handoffs read like a sentence:** `● Boss → ◗ Facilities`, followed by the exact request quoted below.
- **Tool calls become plain English.** `check_stock` shows as *"Checked stock: CC-TEE-WHITE size S: 0 in stock · cost $8 · list $28"*, and `prepare_payment` as *"$2,400 for lease 1, waiting for approval (request #1)"*. The raw audit trail is turned into readable lines.
- **The team roster shows live status.** A working agent's shape gently "breathes" (scales down and up). A finished agent shows its own summary, who it asked, and the tools it used. An agent that wasn't called fades back and says **Not needed**, which also shows whether the Boss avoided calling everyone.

## Resolved tickets

Resolving should feel calm and final, not celebratory:
- In the ticket list, a **thin blue circle with a checkmark that draws itself** (a short stroke animation) next to the word *Resolved*. The big ticket number fades from blue to gray, so open work keeps the visual weight.
- On the floor, the Run button is replaced by an outlined pill stamp, **RESOLVED**, in Yale blue.
- **The Boss's call** appears above the conversation in a white card with a blue edge and the Boss's circle, so the outcome is the first thing you read.

## Cash

- The checking balance is **one large number** in the header, in tabular figures. Nothing else on the page is that big.
- Below it, one quiet line: either "as of 2026-08-31" or, when agents have queued payments, "$2,400 waiting for approval · $1,000 free", so you know what the number will become.
- When you approve a payment, the number **counts down** to the new balance over about a second and briefly turns Yale blue. You see the money leave instead of having a digit silently change. (In testing it went from $3,400 to $1,000 after approving the $2,400 rent.)

## Approvals: the only warm thing on the page

Each payment or purchase order the agents prepare shows up under **Needs you** as a pale mustard card: the amount in big type, what it pays, the agent's reason, and two choices, a solid mustard **Approve** button and a plain **Reject** link. A mustard badge next to "Needs you" counts what's waiting. When nothing is waiting, it just says *"Nothing is waiting for you."* This is the only route where cash moves, and the backend still refuses if there isn't enough.

## Motion: small and purposeful

- New feed lines and summaries **fade in and rise 4px**, so you notice new activity without the page jumping around. The feed scrolls itself only while a run is live.
- While the team works, three tiny agent shapes **hop** in the Run button ("Team working"), and the ticket in the list shows a pulsing dot.
- The resolved checkmark draws itself, and the cash number eases down.
- With nothing to show yet, the five shapes **float** gently above *"The team is quiet."*
- Everything is turned off for people who set "reduce motion" in their system settings.

## Small choices that make it pleasant to use

- **The page polls quickly only when it needs to:** every 1.2 seconds while a run is going and every 5 seconds otherwise. It only asks for events newer than the last one it has, so it stays light.
- **Friendly failure.** If the backend isn't running, a plain banner shows the exact command to start it, with no stack traces.
- **Only one run at a time.** Other tickets' Run buttons say *"Another ticket is running"*, matching the backend's one-run-at-a-time rule that protects cash.
- **History without clutter.** The floor shows the latest run on a ticket and notes how many earlier runs are in the audit trail.
- **Reset shop data** is a small underlined link (with a confirm prompt) rather than a big red button, because it's a tool for rehearsal, not daily work.
- **Favicon:** a blue circle and a mustard square, the whole design system in 32 pixels.
