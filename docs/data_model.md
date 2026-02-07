# Data Model

## Entities
- Organization
- OrganizationSetting
- User
- Company
- Actual (monthly canonical line item)
- Upload (raw file)
- Mapping (source account → canonical category)
- Scenario
- AuditLog

## ERD (ASCII)
```
Organization 1---* User
Organization 1---* Company 1---* Actual
Organization 1---1 OrganizationSetting
Company 1---* Scenario
Company 1---* Upload
Company 1---* Mapping
Organization 1---* AuditLog
```

## Canonical Categories
- Revenue
- COGS
- Sales & Marketing
- R&D
- G&A
- Other OpEx
- Cash
