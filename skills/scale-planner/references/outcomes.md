# Outcomes

Each component gets exactly one outcome. The outcome decides the shape of its video segment (see the explainer-video teaching template), so a wrong outcome makes a misleading segment.

## keep
The current or simplest option meets the contract across the whole range.
- Use when no axis reaches its limit in range.
- Write one option, `breaks_when: null`, and put the tempting upgrade and why it is wrong into `teaching_moment`.
- Failure sign: you are adding a second option only because a bigger option exists.

## substitute_up
A larger option becomes necessary at a point inside the range.
- Use when the binding axis crosses a limit inside the range and the larger option keeps the contract.
- One option per band that the axis crosses. Two is common. Do not pad to three.
- Failure sign: `breaks_when` values are guesses with no evidence and no conditions.

## substitute_down
The input design is larger than the range needs.
- Use when the given option's cost (money, operations, team skill, change speed) is out of proportion to the binding axis at the user's scale.
- First option: the smaller one that still keeps the contract. Second option: the given design, with the point where it starts to pay off.
- Failure sign: the smaller option silently drops a contract property.

## split
One component is doing two jobs whose axes pull in different directions.
- Use when two axes bind at different points, or when reads and writes, or hot and cold data, need different options.
- Options show the single component first, then the two parts with their own picks.
- Failure sign: the split adds a consistency problem between the two parts that nobody names. Name it in `cost`.

## remove
Nothing in range needs the component, or another component already does its job.
- Use when the job is empty at this scale, or duplicated.
- One option: what takes over the job. Its `cost` names what is lost.
- Failure sign: the removed component carried a contract property (for example, durability) that is now silently gone.

## Mix check
In a design with four or more components, all components sharing one outcome is rare. When it happens, re-check each one against the input. It can be correct (for example, a deliberately overbuilt design reviewed for a tiny team), and then the plan should say so.
