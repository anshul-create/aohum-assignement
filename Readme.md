graph TD
    Client[Client / API Consumer] -->|HTTP Requests| API[Django REST API]

    subgraph "Django Application"
        API --> Auth[Authentication & JWT]
        API --> Users[Users App]
        API --> Events[Events App]
        API --> Enrollments[Enrollments App]

        %% Authentication flow
        Auth -->|Signup / Login / Refresh| Users
        Auth -->|Verify JWT| Events
        Auth -->|Verify JWT| Enrollments

        %% Users
        Users -->|Create / Verify OTP| UserDB[(UserProfile, EmailOTP)]
        Users -->|Email sending| Email

        %% Events
        Events -->|CRUD + Search| EventDB[(Event)]
        Events -->|My Events| EventDB
        Events -->|Enrollment counts| Enrollments

        %% Enrollments
        Enrollments -->|Enroll / Cancel / List| EnrollmentDB[(Enrollment)]
        Enrollments -->|select_for_update (lock)| EventDB
        Enrollments -->|UniqueConstraint(event, seeker, status='enrolled')| EnrollmentDB

        %% Critical constraints notes
        EventDB -->|Capacity check| Enrollments
    end

    %% External dependencies
    subgraph External
        Email[Email Service\n(console/file backend)]
    end

    %% Legend / annotations
    classDef default fill:#f9f,stroke:#333,stroke-width:2px;
    classDef db fill:#bbf,stroke:#333,stroke-width:2px;
    classDef external fill:#bfb,stroke:#333,stroke-width:2px;
    class UserDB,EventDB,EnrollmentDB db;
    class Email external;
