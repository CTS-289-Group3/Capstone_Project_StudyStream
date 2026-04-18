# StudyStream Database ERD

Updated from current Django model definitions on 2026-04-18.

## Scope

This ERD covers the application domain schema and ownership links to Django users.

- Accounts app tables: accounts_*
- Core app tables: core_*
- Owner/auth table: auth_user

## Mermaid ER Diagram

```mermaid
erDiagram
    AUTH_USER {
        int id PK
        string username
        string email
    }

    ACCOUNTS_PROFILE {
        int id PK
        int user_id FK
        string display_name
        string avatar_text
        string major
        string year
    }

    ACCOUNTS_SEMESTER {
        int id PK
        int user_id FK
        string name
        date start_date
        date end_date
        bool is_active
        datetime created_at
        datetime updated_at
    }

    ACCOUNTS_COURSE {
        int id PK
        int semester_id FK
        int user_id FK
        string course_code
        string course_name
        string color_hex
        string professor_name
        string professor_email
        string meeting_times
        datetime created_at
        datetime updated_at
    }

    ACCOUNTS_TAG {
        int id PK
        int user_id FK
        string name
        string color_hex
    }

    ACCOUNTS_ASSIGNMENT {
        int id PK
        uuid assignment_id
        int course_id FK
        int user_id FK
        string title
        string assignment_type
        datetime due_date
        string due_time
        decimal estimated_hours
        string status
        string priority_level
        bool is_major_project
        bool contributes_to_workload
        int completion_percentage
        datetime started_at
        datetime completed_at
        datetime created_at
        datetime updated_at
    }

    ACCOUNTS_ASSIGNMENTSUBTASK {
        int id PK
        uuid subtask_id
        int assignment_id FK
        string title
        int step_order
        datetime due_date
        string due_time
        decimal estimated_hours
        string status
        int completion_percentage
        datetime created_at
        datetime updated_at
    }

    ACCOUNTS_TIMEBLOCK {
        int id PK
        int user_id FK
        int assignment_id FK
        string title
        datetime start_time
        datetime end_time
        string status
        bool is_recurring
        string recurrence
        datetime created_at
        datetime updated_at
    }

    ACCOUNTS_ASSIGNMENT_TAGS {
        int id PK
        int assignment_id FK
        int tag_id FK
    }

    CORE_WORKSPACE {
        int id PK
        int user_id FK
        string name
        datetime created_at
    }

    CORE_PERSONALEVENT {
        int id PK
        int user_id FK
        string title
        date event_date
        time start_time
        time end_time
        string location
        string color_hex
        datetime created_at
    }

    CORE_WORKSHIFT {
        int id PK
        uuid shift_id
        int user_id FK
        string employer_name
        date shift_date
        time start_time
        time end_time
        datetime shift_start
        datetime shift_end
        string location
        bool is_confirmed
        bool is_recurring
        string recurrence_pattern
        string color_hex
        datetime created_at
        datetime updated_at
    }

    CORE_RECURRINGWORKSHIFT {
        int id PK
        int user_id FK
        string name
        time start_time
        time end_time
        string location
        string recurrence_pattern
        bool is_active
        datetime created_at
        datetime updated_at
    }

    CORE_RECURRINGWORKLOCATION {
        int id PK
        int user_id FK
        string name
        bool is_active
        datetime created_at
        datetime updated_at
    }

    CORE_RECURRINGJOBTITLE {
        int id PK
        int user_id FK
        string title
        bool is_active
        datetime created_at
        datetime updated_at
    }

    CORE_RECURRINGPERSONALEVENT {
        int id PK
        int user_id FK
        string title
        date start_date
        time start_time
        time end_time
        string location
        string recurrence_pattern
        string weekdays
        int monthly_day
        bool is_active
        datetime created_at
        datetime updated_at
    }

    CORE_WORKLOADANALYSIS {
        uuid analysis_id PK
        int user_id FK
        date week_start_date
        int week_number
        int year
        decimal total_class_hours
        decimal total_work_hours
        decimal total_assignment_hours
        decimal available_study_hours
        decimal utilization_ratio
        string week_status
        int assignment_count
        int major_assignment_count
        bool deadline_cluster_detected
        bool is_overloaded
        bool alert_sent
        datetime alert_sent_at
        datetime created_at
        datetime updated_at
    }

    AUTH_USER ||--|| ACCOUNTS_PROFILE : has
    AUTH_USER ||--o{ ACCOUNTS_SEMESTER : owns
    AUTH_USER ||--o{ ACCOUNTS_COURSE : owns
    AUTH_USER ||--o{ ACCOUNTS_TAG : owns
    AUTH_USER ||--o{ ACCOUNTS_ASSIGNMENT : owns
    AUTH_USER ||--o{ ACCOUNTS_TIMEBLOCK : owns

    ACCOUNTS_SEMESTER ||--o{ ACCOUNTS_COURSE : contains
    ACCOUNTS_COURSE ||--o{ ACCOUNTS_ASSIGNMENT : has
    ACCOUNTS_ASSIGNMENT ||--o{ ACCOUNTS_ASSIGNMENTSUBTASK : has
    ACCOUNTS_ASSIGNMENT ||--o{ ACCOUNTS_TIMEBLOCK : scheduled_in
    ACCOUNTS_ASSIGNMENT ||--o{ ACCOUNTS_ASSIGNMENT_TAGS : tagged
    ACCOUNTS_TAG ||--o{ ACCOUNTS_ASSIGNMENT_TAGS : labels

    AUTH_USER ||--o{ CORE_WORKSPACE : owns
    AUTH_USER ||--o{ CORE_PERSONALEVENT : owns
    AUTH_USER ||--o{ CORE_WORKSHIFT : owns
    AUTH_USER ||--o{ CORE_RECURRINGWORKSHIFT : owns
    AUTH_USER ||--o{ CORE_RECURRINGWORKLOCATION : owns
    AUTH_USER ||--o{ CORE_RECURRINGJOBTITLE : owns
    AUTH_USER ||--o{ CORE_RECURRINGPERSONALEVENT : owns
    AUTH_USER ||--o{ CORE_WORKLOADANALYSIS : owns
```

## Table Inventory

### Domain tables

1. accounts_profile
2. accounts_semester
3. accounts_course
4. accounts_tag
5. accounts_assignment
6. accounts_assignmentsubtask
7. accounts_timeblock
8. accounts_assignment_tags (M2M through table)
9. core_workspace
10. core_personalevent
11. core_workshift
12. core_recurringworkshift
13. core_recurringworklocation
14. core_recurringjobtitle
15. core_recurringpersonalevent
16. core_workloadanalysis

### Framework/auth tables

1. auth_user
2. auth_group
3. auth_group_permissions
4. auth_permission
5. auth_user_groups
6. auth_user_user_permissions
7. django_admin_log
8. django_content_type
9. django_migrations
10. django_session

## Key Constraints and Notes

- accounts_profile uses one-to-one ownership with auth_user.
- accounts_assignment_tags supports Assignment <-> Tag many-to-many mapping.
- core_workloadanalysis enforces a unique weekly record per user via unique constraint on (user, week_start_date).
- Recurring schedules are template records in core_recurringworkshift and core_recurringpersonalevent and are expanded in application logic.
