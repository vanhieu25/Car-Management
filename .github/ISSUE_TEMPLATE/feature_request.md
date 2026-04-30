name: Feature Request

description: Suggest an idea for this project

body:
  - type: markdown
    attributes:
      value: |
        ## Feature Description
        Describe the feature clearly.

  - type: textarea
    id: problem
    attributes:
      label: Problem Statement
      description: What problem does this solve?
    validations:
      required: true

  - type: textarea
    id: solution
    attributes:
      label: Proposed Solution
      description: How should it work?
    validations:
      required: true

  - type: textarea
    id: alternatives
    attributes:
      label: Alternatives Considered
      description: Other solutions considered

  - type: checkboxes
    id: breaking
    attributes:
      label: Breaking Changes
      options:
        - label: This change introduces breaking changes
          required: false