Variables Tab
=============

Variables are used to handle the state of various workflow related
information that doesn't justify a state of it's own. The default CMF
workflows use variables to track status history comments, and store the the
last transition, who initiated it and when, for example. From the variables
tab it's possible to add new variables, and rename and delete existing
variables.

The list of existing variables also displays a summary of each variable's
description, catalog availability, workflow status, default value or
expression and any access guards. You can click through to each variable to
configure it's details.

In each variable's property tab you can set the variable's description and a
collection of properties the define the variable's behaviour, as follows:

**Make available to catalog** --
  Just as it says, it makes this variable available to the catalog for
  indexing, however it doesn't automatically create an index for it - you have
  to create one by hand that reflects the content of the variable. Once
  indexed, you can query the catalog for content that has a particular value in
  is variable, and update the variable by workflow actions.

**Store in workflow status** --
  The workflow status is a mapping that exists in the state_change object that
  is passed to scripts and available to expressions.

**Variable update mode** --
  Select whether the variable is updated on every transition (in which case,
  you should set a default expression), or whether it should only update if a
  transition or state sets a value.

**Default value** --
  Set the default value to some string.

**Default expression** --
  This is a TALES expression (as described in Expressions) and overrides the
  default value.

**Guards** --
  See the :doc:`Guards`.

**State variable** --
  stores the name of the variable the current state of the content is stored
  in. CMF uses 'review_state' by default, and will have already created a
  FieldIndex for it. The state variable is effectively a variable with "Make
  available to catalog" set, a default value of whatever the initial state is
  and a default expression that sets to the new state on every transition.
