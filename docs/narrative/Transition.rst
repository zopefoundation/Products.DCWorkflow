Transitions Tab
===============

Transitions are the actions that move content from one state in the workflow
to another. From the transitions tab it's possible to add new transitions,
and rename and delete existing transitions.

The list of existing transitions also displays a summary of each transition's
title, description, destination state, trigger, guards, and action box entry.
You can click through each transition to access their details.

Within a transition's properties tab you can set the title, and a collection
of properties the define the transtion's behaviour, as follows:

**Destination state** --
 selected from all the states defined in the states tab. A transition can
 remain in state, which is useful for a reviewer adding comments to the review
 history, but not taking any action, updating some variable, or invoking
 scripts.

**Trigger type**  --
 There are two types:

 * User actions are the familiar user initiated transitions activated by
   actions in the action box.

 * Automatic transitions are executed any time other workflow events occur;
   so if a user action results in the content moving to a state that has
   automatic transitions, they will be executed. (You should use mutually
   exclusive guards to prevent indeterminate behavior.)


**Scripts** --
 Perform complicated behaviours either before or after the transition takes
 place. Scripts of all kinds are defined in the workflow's scripts tab.
 Scripts called from here must accept only one argument; a 'status_change'
 object. See Expressions for more details.

**Guards and Action boxes** --
 See the :doc:`Guards` and :doc:`ActionBoxes` sections for specific details
 about those fields. Note that automatic transitions don't need the action box
 fields to be filled out.

 What the action should link to.

In the transition's variables tab, you can add, change and delete variables
that you want to assign a value to, when the transition is executed. The
available variables are set in the workflow's variables tab, and the value is
a TALES expression (see Expressions for more details).
