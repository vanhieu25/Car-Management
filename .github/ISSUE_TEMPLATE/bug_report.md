name: Bug Report

description: Create a report to help us improve

body:
  - type: markdown
    attributes:
      value: |
        ## Bug Description
        Describe the bug clearly.

  - type: textarea
    id: steps
    attributes:
      label: Steps to Reproduce
      description: How to reproduce the bug
      placeholder: |
        1. Go to '...'
        2. Click on '...'
        3. See error
    validations:
      required: true

  - type: textarea
    id: expected
    attributes:
      label: Expected Behavior
      description: What should happen
    validations:
      required: true

  - type: textarea
    id: actual
    attributes:
      label: Actual Behavior
      description: What actually happens
    validations:
      required: true

  - type: input
    id: environment
    attributes:
      label: Environment
      description: OS, Python version, etc.
      placeholder: Windows 11, Python 3.11

  - type: checkboxes
    id: logs
    attributes:
      label: Logs
      options:
        - label: I have attached relevant logs
          required: false