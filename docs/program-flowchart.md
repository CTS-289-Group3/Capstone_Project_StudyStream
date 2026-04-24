# StudyStream Program Flowchart

This diagram shows the high-level runtime flow through authentication, dashboard actions, persistence, and loop/exit behavior.

## Mermaid Flowchart

```mermaid
flowchart TD
    A([Start Program]) --> B[Initialize Settings]
    B --> C{User Logged In?}
    C -- No --> D[Show Login or Register]
    D --> E{Valid Credentials?}
    E -- No --> D
    E -- Yes --> F[Load Dashboard]
    C -- Yes --> F

    F --> G[User Chooses Action]

    G --> H[Create or Edit Assignment]
    G --> I[Run Workload Analysis]
    G --> J[View Schedule and Events]

    H --> K[Save Changes to Database]
    I --> K
    J --> K

    K --> L{Continue Session?}
    L -- Yes --> G
    L -- No --> M([End Program])
```

## Notes

- Decision nodes (`{...}`) represent conditional branching.
- Rounded endpoints (`([ ... ])`) mark start and end states.
- This is a high-level flow and can be expanded into app-specific sub-flows.
