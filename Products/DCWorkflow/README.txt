=====================
 Products.DCWorkflow
=====================

This product provides fully customizable workflows for the CMF 
portal_workflow tool.

Usage
=====

To see an example, after installing DCWorkflow, using the "Contents"
tab of your portal_workflow instance add a "CMF default workflow (rev 2)"
instance. 

Developing a workflow
=====================

This tool is easiest to use if you draw a state diagram first.  Your
diagram should have:

- States (bubbles)

- Transitions (arrows)

- Variables (both in states and transitions)

Remember to consider all the states your content can be in.  Consider
the actions users will perform to make the transitions between states.
And consider not only who will be allowed to perform what functions,
but also who will be *required* to perform certain functions.

On the "States" tab, add a state with a simple ID for each state on
your diagram.  On the "Transitions" tab, add a transition with a simple
ID for each group of arrows that point to the same state and have
similar characteristics.  Then for each state choose which transitions
are allowed to leave that state.

Variables are useful for keeping track of things that aren't very well
represented as separate states, such as counters or information about
the action that was last performed.  You can create variables that get
stored alongside the workflow state and you can make those variables
available in catalog searches.  Some variables, such as the review
history, should not be stored at all.  Those variables are accessible
through the getInfoFor() interface.

Worklists are a way to make people aware of tasks they are required
to perform.  Worklists are implemented as a catalog query that puts
actions in the actions box when there is some task the user needs to
perform.  Most of the time you just need to enter a state ID,
a role name, and the information to put in the actions box.

You can manage all of the actions a user can perform on an object by
setting up permissions to be managed by the workflow.  Using the
"Permissions" tab, select which permissions should be state-dependent.
Then in each state, using the "permissions" tab, set up the
role to permission mappings appropriate for that state.

Finally, you can extend the workflow with scripts.  Scripts can be
External Methods, Python Scripts, DTML methods, or any other callable
Zope object.  They are accessible by name in expressions.  Scripts
are invoked with a state_change object as the first argument; see
expressions.stx.

Once you've crafted your workflow, you hook it up with a content type
by using the portal_workflow top-level "Workflows" tab.  Specify the
workflow name in the target content type's box.
