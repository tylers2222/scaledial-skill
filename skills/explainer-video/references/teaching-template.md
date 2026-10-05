# Teaching template

One segment per plan component, in `plan.order`. A segment is 4 to 10 beats (about 30 to 90 seconds). The segment shape depends on the component's `outcome`. Do not force every component into the same shape. A video where every segment is "simple thing breaks, bigger thing replaces it" teaches one idea many times.

## Shared opening and closing

Every segment opens and closes the same way, so the viewer always knows where they are.

- **Open: the job.** Name the component by what it does, not by its product. "Something has to get each price update from the exchange into the strategy." Show the component in its place on the full diagram.
- **Contract.** Say the one or two contract properties that a substitute must keep. These are what make a later substitution valid or invalid.
- **Close: handoff.** One beat that names the next component and why it comes next.

## Middle, by outcome

### substitute_up
1. Start at the smallest band in the user's range. Show the simple option and why it is right there.
2. Turn the scale dial up on the **binding axis**. Show the simple option failing in a way the viewer can see: a queue that grows, a latency bar that crosses a budget, a disk that fills.
3. Swap in the next option in place. Say what it fixes and what it costs.
4. Repeat for each band. Stop at the top of the user's range.
5. Turn the dial back down. Show why the big option is a liability at small scale (cost, operations, team skill).

### substitute_down
1. Start from the design as given. Name what it was built for.
2. Show the user's actual scale on the dial. Show the cost of the big option at that scale: idle capacity, operations work, team hours.
3. Swap in the smaller option. Show that it still keeps the contract.
4. Name the signal that would mean it is time to move back up.

### keep
1. Show the simple option.
2. Turn the dial up through the user's whole range. Show that the binding axis stays inside its limit.
3. Name the tempting upgrade and why it is wrong here. This is the teaching moment, and it is often the most useful segment in the video.
4. Name the condition outside the range where the answer would change.

### split
1. Show the single component doing two jobs.
2. Turn the dial up. Show the two jobs pulling in different directions on different axes.
3. Split the box into two. Give each its own option and show which axis each one now follows.

### remove
1. Show the component and what it was added for.
2. Show that at the user's scale nothing needs it, or another component already does its job.
3. Remove it from the diagram and show the simpler path.

## Visual grammar (keep it the same across segments)

- One persistent diagram. Zoom into the current component. Do not redraw the system for each segment.
- One scale dial, always in the same place, labelled in the binding axis's units.
- Substitution is a morph in place (`swap`), never a cut to a new screen.
- Cost appears as a short list in one fixed corner. It replaces the previous list.

## Ending

A summary table: one row per component, columns for the job, the binding axis, and the option per band. Then one beat on the single most surprising teaching moment in the video.
