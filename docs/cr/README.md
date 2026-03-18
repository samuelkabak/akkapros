# Change Request System

This directory contains Change Requests (CRs) describing planned changes to the project.

A Change Request documents:

- what change is requested
- why the change is needed
- how the change should be implemented
- how the result will be verified

CRs provide lightweight documentation and help structure development work.

They are useful both for individual developers and small teams collaborating through GitHub.

[CR index](index.md) 

---------------------------------------------------------------------

# Directory Structure

Each Change Request lives in its own directory.

Structure:

docs/
  cr/
    000-cr-template/
      CR.md
      tasks.md
      notes.md (optional)

    001-short-title/
      CR.md
      tasks.md
      notes.md (optional)

Example:

docs/
  cr/
    001-initial-authentication/
      CR.md
      tasks.md

    002-rate-limiting/
      CR.md
      tasks.md
      notes.md


---------------------------------------------------------------------

# Template Directory

The folder:

docs/cr/000-cr-template/

contains templates used when creating a new Change Request.

Files:

CR.md  
Main Change Request document.

tasks.md  
Optional task list used to track implementation steps.

notes.md (optional)  
Design notes, investigation results, or architecture discussions.

When creating a new CR, copy these files from the template directory.


---------------------------------------------------------------------

# Naming Rules

CR folders use the format:

NNN-short-kebab-title

Examples:

001-initial-authentication  
002-rate-limiter  
003-support-oauth-login  

Where:

NNN is a sequential number.

---------------------------------------------------------------------

# Directory Naming Convention

All documentation directories use lowercase names.

Examples:

docs/
  cr/
  adr/

Change Request folders follow the format:

NNN-short-kebab-title

Examples:

001-initial-authentication
002-rate-limiter
003-support-oauth-login

Rules:

- use lowercase
- use hyphens between words
- keep titles short but descriptive

---------------------------------------------------------------------

# CR Status

Each Change Request should have a status.

Draft  
Idea or proposal being defined.

Approved  
The change has been reviewed and accepted.

In Progress  
Implementation has started.

Done  
The change has been implemented and merged.


---------------------------------------------------------------------

# When to Create a Change Request

Create a CR when making meaningful changes such as:

- new features
- architectural changes
- behavior changes
- important refactoring
- complex bug fixes

Small fixes or trivial changes usually do not require a CR.


---------------------------------------------------------------------

# Implementation Workflow

Typical workflow:

1. Create a new CR directory
2. Copy the templates from `000-cr-template`
3. Fill in CR.md
4. Break down work in tasks.md
5. Implement the change
6. Verify the acceptance criteria
7. Mark the CR as Done

Pull requests should reference the CR ID.

Example:

Implements CR-004


---------------------------------------------------------------------

# Creating a New Change Request

Steps:

1. Determine the next CR number.

2. Create a directory.

Example:

docs/cr/005-add-webhook-support/

3. Copy the template files from:

docs/cr/000-cr-template/

4. Refer to ADRs in docs/adr/* as architecture guidelines

5. Update the content of:

CR.md  
tasks.md (optional)
notes.md (optional)


6. Link CR.md it in index.md, the latest CR first
> Example:
> [NNN. Short Kebab Title](NNN-short-kebab-title/CR.md) - Status

---------------------------------------------------------------------

# CR Files

CR.md

Main document describing the change.

It should explain:

- the problem
- the proposed solution
- the technical design
- acceptance criteria


tasks.md

Optional checklist used to track implementation work.


notes.md

Optional document for:

- design exploration
- architecture notes
- alternative approaches
- investigation results


---------------------------------------------------------------------

# Writing a Good Change Request

A good CR should:

- clearly explain the problem
- define the intended behavior
- describe the implementation approach
- list affected parts of the system
- define acceptance criteria

Keep descriptions concise and practical.


---------------------------------------------------------------------

# Instructions for Automated Tools or Assistants

When asked to create a new Change Request:

1. Determine the next available CR number.

2. Create a directory:

docs/cr/NNN-short-title/

3. Copy the templates from:

docs/cr/000-cr-template/

4. Update CR.md with the new change description.

5. Update tasks.md with implementation steps if applicable.

6. Optionally create or update notes.md for design discussions.

The CR should contain enough information so that another developer can implement the change without additional clarification.


---------------------------------------------------------------------

# Example Request

Example instruction that may be used:

Create a new Change Request following the principles in docs/cr/README.md to implement the following features:

- add webhook support
- store webhook delivery history
- retry failed webhook events

The expected result is:

- a new CR directory
- a completed CR.md
- an optional tasks.md
- clear acceptance criteria